import json
import os
import sys
import networkx as nx
import pandas as pd
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
PROC_DIR = os.path.join(PROJECT_ROOT, "data/processed")


@st.cache_data
def load_summary_and_metrics():
    """
    Load all processed Phase 4 datasets and metrics.
    Returns:
        summary (dict): Parsed graph_summary.json.
        wallet_metrics (pd.DataFrame): wallet_graph_metrics.csv.
        ip_metrics (pd.DataFrame): ip_graph_metrics.csv.
        tx_features (pd.DataFrame): transaction_features.csv.
        corr_events (pd.DataFrame): correlated_events.csv.
        wallet_metrics_map (dict): wallet_id -> dict of metrics.
        ip_metrics_map (dict): ip_address -> dict of metrics.
    """
    summary_path = os.path.join(PROC_DIR, "graph_summary.json")
    wallet_metrics_path = os.path.join(PROC_DIR, "wallet_graph_metrics.csv")
    ip_metrics_path = os.path.join(PROC_DIR, "ip_graph_metrics.csv")
    tx_features_path = os.path.join(PROC_DIR, "transaction_features.csv")
    corr_events_path = os.path.join(PROC_DIR, "correlated_events.csv")

    summary = {}
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    wallet_metrics = pd.read_csv(wallet_metrics_path) if os.path.exists(wallet_metrics_path) else pd.DataFrame()
    ip_metrics = pd.read_csv(ip_metrics_path) if os.path.exists(ip_metrics_path) else pd.DataFrame()
    tx_features = pd.read_csv(tx_features_path) if os.path.exists(tx_features_path) else pd.DataFrame()
    corr_events = pd.read_csv(corr_events_path) if os.path.exists(corr_events_path) else pd.DataFrame()

    wallet_metrics_map = {}
    if not wallet_metrics.empty and "wallet_id" in wallet_metrics.columns:
        for _, r in wallet_metrics.iterrows():
            wallet_metrics_map[str(r["wallet_id"]).strip()] = r.to_dict()

    ip_metrics_map = {}
    if not ip_metrics.empty and "ip_address" in ip_metrics.columns:
        for _, r in ip_metrics.iterrows():
            ip_metrics_map[str(r["ip_address"]).strip()] = r.to_dict()

    return summary, wallet_metrics, ip_metrics, tx_features, corr_events, wallet_metrics_map, ip_metrics_map


@st.cache_resource
def load_graph_object(graph_type="investigation"):
    """
    Load GraphML graph structure with caching across sessions.
    Args:
        graph_type (str): 'investigation', 'wallet', or 'ip'.
    Returns:
        nx.MultiDiGraph / nx.DiGraph: In-memory NetworkX graph.
    """
    filename_map = {
        "investigation": "investigation_graph.graphml",
        "wallet": "wallet_graph.graphml",
        "ip": "ip_graph.graphml"
    }

    graph_file = os.path.join(PROC_DIR, filename_map.get(graph_type, "investigation_graph.graphml"))
    if os.path.exists(graph_file):
        try:
            return nx.read_graphml(graph_file)
        except Exception:
            pass

    # Fallback to running graph pipeline if file missing
    from src.graph.run_graph_pipeline import run_graph_pipeline
    wallet_g, ip_g, inv_g = run_graph_pipeline()
    if graph_type == "wallet":
        return wallet_g
    elif graph_type == "ip":
        return ip_g
    return inv_g


@st.cache_data
def get_hourly_activity_data(tx_features: pd.DataFrame, corr_events: pd.DataFrame):
    """
    Aggregate transactions and network observations into hourly time series for charts.
    """
    tx_hourly = pd.DataFrame(columns=["timestamp", "count"])
    if not tx_features.empty and "timestamp" in tx_features.columns:
        df = tx_features.copy()
        df["dt"] = pd.to_datetime(df["timestamp"])
        tx_hourly = df.set_index("dt").resample("2h").size().reset_index(name="count")
        tx_hourly.rename(columns={"dt": "timestamp"}, inplace=True)

    obs_hourly = pd.DataFrame(columns=["timestamp", "count"])
    if not corr_events.empty and "timestamp_obs" in corr_events.columns:
        df_obs = corr_events.copy()
        df_obs["dt"] = pd.to_datetime(df_obs["timestamp_obs"])
        obs_hourly = df_obs.set_index("dt").resample("2h").size().reset_index(name="count")
        obs_hourly.rename(columns={"dt": "timestamp"}, inplace=True)

    return tx_hourly, obs_hourly


def get_node_intelligence_data(
    G: nx.MultiDiGraph,
    node_id: str,
    wallet_metrics_map: dict,
    ip_metrics_map: dict,
    tx_features_df: pd.DataFrame
) -> dict:
    """
    Extract comprehensive analyst intelligence for a selected node in the investigation graph.
    """
    if node_id not in G:
        return {"found": False, "node_id": node_id}

    node_data = G.nodes.get(node_id, {})
    ntype = node_data.get("node_type", "unknown").lower()
    raw_label = node_data.get("label", node_id)

    # Neighbors
    in_neighbors = list(G.predecessors(node_id))
    out_neighbors = list(G.successors(node_id))
    all_neighbors = list(set(in_neighbors) | set(out_neighbors))

    connected_entities = [n for n in all_neighbors if n.startswith("entity:")]
    connected_wallets = [n for n in all_neighbors if n.startswith("wallet:")]
    connected_txs = [n for n in all_neighbors if n.startswith("tx:")]
    connected_ips = [n for n in all_neighbors if n.startswith("ip:")]

    signals = []
    structural_metrics = {}

    if ntype == "wallet":
        wallet_id = node_data.get("wallet_id", raw_label)
        w_meta = wallet_metrics_map.get(wallet_id, {})
        in_deg = int(w_meta.get("in_degree", len(in_neighbors)))
        out_deg = int(w_meta.get("out_degree", len(out_neighbors)))
        pr = float(w_meta.get("pagerank", 0.0))
        bc = float(w_meta.get("betweenness_centrality", 0.0))

        structural_metrics = {
            "In-Degree": in_deg,
            "Out-Degree": out_deg,
            "PageRank": f"{pr:.6f}" if pr else "N/A",
            "Betweenness": f"{bc:.6f}" if bc else "N/A"
        }

        # Dynamic signals based on actual metrics
        if in_deg >= 7:
            signals.append("High In-Degree Receiver — Aggregates incoming flows from multiple wallets")
        if out_deg >= 7:
            signals.append("High Out-Degree Distributor — Fans out transfers to multiple targets")
        if bc >= 0.03:
            signals.append("High Bridge Centrality — Critical topological conduit between transaction clusters")
        if pr >= 0.02:
            signals.append("High Structural Influence — Elevated PageRank prestige rank in wallet graph")
        if len(connected_entities) > 1:
            signals.append(f"Multi-Entity Association — Associated with {len(connected_entities)} distinct entities")

    elif ntype == "transaction":
        txid = node_data.get("txid", raw_label)
        amount = float(node_data.get("amount", 0.0))
        fee = float(node_data.get("fee", 0.0))
        pattern = str(node_data.get("pattern_label", "normal"))
        script = str(node_data.get("script_type", "N/A"))

        structural_metrics = {
            "Amount": f"{amount:,.4f} BTC",
            "Fee": f"{fee:.6f} BTC",
            "Script": script,
            "Pattern": pattern
        }

        if pattern == "high_value_anomaly":
            signals.append("High-Value Transfer Flag — Transaction volume exceeds standard statistical threshold")
        elif pattern == "high_frequency_anomaly":
            signals.append("Rapid Velocity Transfer — Characterized by burst propagation and short spacing")
        elif pattern == "peeling_chain":
            signals.append("Peeling Chain Pattern — Repeated asymmetric change address distribution")
        else:
            signals.append("Standard Propagation — Regular baseline transaction structure")

        if len(connected_ips) >= 4:
            signals.append(f"Wide P2P Dissemination — Correlated across {len(connected_ips)} distinct IP nodes")

    elif ntype == "ip":
        ip_addr = node_data.get("ip_address", raw_label)
        ip_meta = ip_metrics_map.get(ip_addr, {})
        in_deg = int(ip_meta.get("in_degree", len(in_neighbors)))
        out_deg = int(ip_meta.get("out_degree", len(out_neighbors)))
        pr = float(ip_meta.get("pagerank", 0.0))

        structural_metrics = {
            "In-Degree": in_deg,
            "Out-Degree": out_deg,
            "PageRank": f"{pr:.6f}" if pr else "N/A",
            "Role": str(node_data.get("node_type_meta", "peer_node"))
        }

        if in_deg + out_deg >= 65:
            signals.append("High-Throughput P2P Relay — In top tier of total network observations")
        if pr >= 0.023:
            signals.append("Primary Propagation Backbone — Top-tier PageRank structural network prominence")
        if node_data.get("entity_id") and node_data.get("entity_id") != "unmapped":
            signals.append(f"Entity Attribution — Mapped to {node_data.get('entity_id')}")

    elif ntype == "entity":
        entity_id = node_data.get("entity_id", raw_label)
        structural_metrics = {
            "Controlled Wallets": len(connected_wallets),
            "Direct Links": len(all_neighbors)
        }
        signals.append(f"Synthetic Entity Entity Umbrella — Directly controls {len(connected_wallets)} wallet nodes")

    if not signals:
        signals.append("Nominal Activity — Standard baseline topology metrics")

    return {
        "found": True,
        "node_id": node_id,
        "node_type": ntype,
        "label": raw_label,
        "data": node_data,
        "metrics": structural_metrics,
        "signals": signals,
        "connected_entities": connected_entities,
        "connected_wallets": connected_wallets,
        "connected_txs": connected_txs,
        "connected_ips": connected_ips,
        "total_neighbors": len(all_neighbors)
    }
