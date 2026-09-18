import os
import sys
import pandas as pd

# Ensure repository root is in python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.graph.exporter import export_graph_outputs
from src.graph.investigation_graph import build_investigation_graph
from src.graph.ip_graph import build_ip_graph
from src.graph.metrics import calculate_graph_summary, calculate_ip_metrics, calculate_wallet_metrics
from src.graph.wallet_graph import build_wallet_graph
from src.ingestion.loader import load_raw_data


def run_integrity_checks(
    blockchain_df: pd.DataFrame,
    network_df: pd.DataFrame,
    entity_wallet_df: pd.DataFrame,
    wallet_graph,
    ip_graph,
    investigation_graph,
    wallet_metrics_df: pd.DataFrame,
    ip_metrics_df: pd.DataFrame
):
    """
    Run automated assertions and integrity checks on constructed graphs.
    """
    # 1. Check wallet nodes representation
    expected_wallets = set(blockchain_df["input_wallet"]) | set(blockchain_df["output_wallet"])
    assert set(wallet_graph.nodes()) == expected_wallets, "Integrity Error: Mismatch between blockchain wallets and wallet graph nodes."

    # 2. Check IP nodes representation
    expected_ips = set(network_df["src_ip"]) | set(network_df["dst_ip"])
    assert set(ip_graph.nodes()) == expected_ips, "Integrity Error: Mismatch between network IPs and IP graph nodes."

    # 3. Check node types in investigation graph
    for node, data in investigation_graph.nodes(data=True):
        ntype = data.get("node_type")
        assert ntype in ["wallet", "transaction", "ip", "entity"], f"Integrity Error: Invalid node_type '{ntype}' for node {node}."

        if node.startswith("wallet:"):
            assert ntype == "wallet"
        elif node.startswith("tx:"):
            assert ntype == "transaction"
        elif node.startswith("ip:"):
            assert ntype == "ip"
        elif node.startswith("entity:"):
            assert ntype == "entity"

    # 4. Entity ownership mapping check
    if not entity_wallet_df.empty:
        for _, row in entity_wallet_df.iterrows():
            e_node = f"entity:{row['entity_id']}"
            w_node = f"wallet:{row['wallet_id']}"
            assert investigation_graph.has_edge(e_node, w_node), f"Integrity Error: Missing ground truth ownership edge {e_node} -> {w_node}"

    # 5. Check metrics CSV row counts
    assert len(wallet_metrics_df) == len(expected_wallets), "Integrity Error: Wallet metrics row count mismatch."
    assert len(ip_metrics_df) == len(expected_ips), "Integrity Error: IP metrics row count mismatch."

    print("      All integrity checks passed successfully!")


def run_graph_pipeline(raw_dir: str = "data/raw", processed_dir: str = "data/processed"):
    """
    Execute Phase 4 Graph Construction, Metrics, and Export Pipeline.
    """
    print("[INFO] Starting Phase 4 Graph Construction...\n")

    raw_path = os.path.isabs(raw_dir) and raw_dir or os.path.join(project_root, raw_dir)
    proc_path = os.path.isabs(processed_dir) and processed_dir or os.path.join(project_root, processed_dir)

    # 1. Loading datasets
    print("[1/7] Loading processed and raw datasets...")
    bc_df, net_df, ew_df, ip_df = load_raw_data(data_dir=raw_path)
    print(f"      Blockchain Transactions: {len(bc_df)}")
    print(f"      Network Observations: {len(net_df)}")

    # 2. Building Wallet Graph
    print("\n[2/7] Building wallet transaction graph...")
    wallet_graph = build_wallet_graph(bc_df)
    print(f"      Nodes: {wallet_graph.number_of_nodes()}")
    print(f"      Edges: {wallet_graph.number_of_edges()}")

    # 3. Building IP Graph
    print("\n[3/7] Building IP communication graph...")
    ip_graph = build_ip_graph(net_df)
    print(f"      Nodes: {ip_graph.number_of_nodes()}")
    print(f"      Edges: {ip_graph.number_of_edges()}")

    # 4. Building Combined Investigation Graph
    print("\n[4/7] Building combined investigation graph...")
    inv_graph = build_investigation_graph(bc_df, net_df, ew_df, ip_df)
    summary = calculate_graph_summary(wallet_graph, ip_graph, inv_graph)
    inv_stats = summary["investigation_graph"]

    print(f"      Wallet Nodes: {inv_stats['wallet_nodes']}")
    print(f"      Transaction Nodes: {inv_stats['transaction_nodes']}")
    print(f"      IP Nodes: {inv_stats['ip_nodes']}")
    print(f"      Entity Nodes: {inv_stats['entity_nodes']}")
    print(f"      Total Nodes: {inv_stats['total_nodes']}, Total Edges: {inv_stats['total_edges']}")

    # 5. Calculating Graph Metrics
    print("\n[5/7] Calculating graph metrics...")
    wallet_metrics_df = calculate_wallet_metrics(wallet_graph)
    ip_metrics_df = calculate_ip_metrics(ip_graph)
    print("      Metrics calculated for wallets and IPs.")

    # 6. Exporting Graph Outputs
    print("\n[6/7] Exporting graph outputs...")
    export_graph_outputs(
        wallet_graph=wallet_graph,
        ip_graph=ip_graph,
        investigation_graph=inv_graph,
        wallet_metrics_df=wallet_metrics_df,
        ip_metrics_df=ip_metrics_df,
        summary_dict=summary,
        output_dir=proc_path
    )
    print("      Saved metrics CSVs, GraphML files, and graph_summary.json.")

    # 7. Integrity Checks
    print("\n[7/7] Running integrity checks...")
    run_integrity_checks(bc_df, net_df, ew_df, wallet_graph, ip_graph, inv_graph, wallet_metrics_df, ip_metrics_df)

    print("\n[SUCCESS] Phase 4 completed successfully.")
    return wallet_graph, ip_graph, inv_graph


if __name__ == "__main__":
    run_graph_pipeline()
