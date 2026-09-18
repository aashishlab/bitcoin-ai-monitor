import json
import os
import networkx as nx
import pandas as pd


def _clean_graph_for_graphml(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Clean graph attributes so they can be serialized cleanly to GraphML format.

    Args:
        G (nx.MultiDiGraph): Input graph.

    Returns:
        nx.MultiDiGraph: Graph with GraphML-compatible scalar attributes.
    """
    cleaned_G = G.copy()

    # Clean node attributes
    for node, data in cleaned_G.nodes(data=True):
        for k, v in list(data.items()):
            if v is None:
                data[k] = ""
            elif isinstance(v, (dict, list, tuple, set)):
                data[k] = str(v)

    # Clean edge attributes
    for u, v, k, data in cleaned_G.edges(keys=True, data=True):
        for attr_k, attr_v in list(data.items()):
            if attr_v is None:
                data[attr_k] = ""
            elif isinstance(attr_v, (dict, list, tuple, set)):
                data[attr_k] = str(attr_v)

    return cleaned_G


def export_graph_outputs(
    wallet_graph: nx.MultiDiGraph,
    ip_graph: nx.MultiDiGraph,
    investigation_graph: nx.MultiDiGraph,
    wallet_metrics_df: pd.DataFrame,
    ip_metrics_df: pd.DataFrame,
    summary_dict: dict,
    output_dir: str = "data/processed"
):
    """
    Save Phase 4 graph outputs (CSV, GraphML, JSON) into data/processed/.

    Args:
        wallet_graph (nx.MultiDiGraph): Wallet transaction graph.
        ip_graph (nx.MultiDiGraph): IP communication graph.
        investigation_graph (nx.MultiDiGraph): Combined investigation graph.
        wallet_metrics_df (pd.DataFrame): Calculated wallet metrics.
        ip_metrics_df (pd.DataFrame): Calculated IP metrics.
        summary_dict (dict): Summary statistics.
        output_dir (str): Relative or absolute target output directory.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Export Metrics CSVs
    wallet_metrics_path = os.path.join(output_dir, "wallet_graph_metrics.csv")
    ip_metrics_path = os.path.join(output_dir, "ip_graph_metrics.csv")

    wallet_metrics_df.to_csv(wallet_metrics_path, index=False)
    ip_metrics_df.to_csv(ip_metrics_path, index=False)

    # 2. Export GraphML files
    nx.write_graphml(_clean_graph_for_graphml(investigation_graph), os.path.join(output_dir, "investigation_graph.graphml"))
    nx.write_graphml(_clean_graph_for_graphml(wallet_graph), os.path.join(output_dir, "wallet_graph.graphml"))
    nx.write_graphml(_clean_graph_for_graphml(ip_graph), os.path.join(output_dir, "ip_graph.graphml"))

    # 3. Export JSON summary
    summary_path = os.path.join(output_dir, "graph_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=4)
