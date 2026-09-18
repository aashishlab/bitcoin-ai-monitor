import networkx as nx
import pandas as pd


def _to_simple_digraph(multigraph: nx.MultiDiGraph) -> nx.DiGraph:
    """
    Convert a MultiDiGraph to a simple weighted DiGraph for centrality algorithms.

    Args:
        multigraph (nx.MultiDiGraph): Input MultiDiGraph.

    Returns:
        nx.DiGraph: Simple directed graph with accumulated edge weights.
    """
    G = nx.DiGraph()

    for node, data in multigraph.nodes(data=True):
        G.add_node(node, **data)

    for u, v, data in multigraph.edges(data=True):
        weight = data.get("amount", data.get("weight", 1.0))
        if G.has_edge(u, v):
            G[u][v]["weight"] += weight
            G[u][v]["count"] += 1
        else:
            G.add_edge(u, v, weight=weight, count=1)

    return G


def calculate_wallet_metrics(wallet_graph: nx.MultiDiGraph) -> pd.DataFrame:
    """
    Calculate structural graph metrics for wallet nodes.

    Args:
        wallet_graph (nx.MultiDiGraph): Wallet transaction MultiDiGraph.

    Returns:
        pd.DataFrame: DataFrame containing wallet metrics per row.
    """
    if wallet_graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=[
            "wallet_id", "in_degree", "out_degree", "total_degree",
            "degree_centrality", "pagerank", "betweenness_centrality"
        ])

    simple_G = _to_simple_digraph(wallet_graph)

    # In-degree, Out-degree, Total-degree from MultiDiGraph
    in_deg = dict(wallet_graph.in_degree())
    out_deg = dict(wallet_graph.out_degree())
    total_deg = dict(wallet_graph.degree())

    # Centrality measures on simple graph
    try:
        deg_centrality = nx.degree_centrality(simple_G)
    except Exception:
        deg_centrality = {n: 0.0 for n in simple_G.nodes()}

    try:
        pagerank = nx.pagerank(simple_G, alpha=0.85, max_iter=500)
    except Exception:
        pagerank = {n: 0.0 for n in simple_G.nodes()}

    try:
        betweenness = nx.betweenness_centrality(simple_G)
    except Exception:
        betweenness = {n: 0.0 for n in simple_G.nodes()}

    rows = []
    for node in wallet_graph.nodes():
        rows.append({
            "wallet_id": str(node),
            "in_degree": int(in_deg.get(node, 0)),
            "out_degree": int(out_deg.get(node, 0)),
            "total_degree": int(total_deg.get(node, 0)),
            "degree_centrality": round(float(deg_centrality.get(node, 0.0)), 6),
            "pagerank": round(float(pagerank.get(node, 0.0)), 6),
            "betweenness_centrality": round(float(betweenness.get(node, 0.0)), 6)
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(by="pagerank", ascending=False).reset_index(drop=True)
    return df


def calculate_ip_metrics(ip_graph: nx.MultiDiGraph) -> pd.DataFrame:
    """
    Calculate structural graph metrics for IP nodes.

    Args:
        ip_graph (nx.MultiDiGraph): IP communication MultiDiGraph.

    Returns:
        pd.DataFrame: DataFrame containing IP metrics per row.
    """
    if ip_graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=[
            "ip_address", "in_degree", "out_degree", "total_degree",
            "degree_centrality", "pagerank", "betweenness_centrality"
        ])

    simple_G = _to_simple_digraph(ip_graph)

    in_deg = dict(ip_graph.in_degree())
    out_deg = dict(ip_graph.out_degree())
    total_deg = dict(ip_graph.degree())

    try:
        deg_centrality = nx.degree_centrality(simple_G)
    except Exception:
        deg_centrality = {n: 0.0 for n in simple_G.nodes()}

    try:
        pagerank = nx.pagerank(simple_G, alpha=0.85, max_iter=500)
    except Exception:
        pagerank = {n: 0.0 for n in simple_G.nodes()}

    try:
        betweenness = nx.betweenness_centrality(simple_G)
    except Exception:
        betweenness = {n: 0.0 for n in simple_G.nodes()}

    rows = []
    for node in ip_graph.nodes():
        rows.append({
            "ip_address": str(node),
            "in_degree": int(in_deg.get(node, 0)),
            "out_degree": int(out_deg.get(node, 0)),
            "total_degree": int(total_deg.get(node, 0)),
            "degree_centrality": round(float(deg_centrality.get(node, 0.0)), 6),
            "pagerank": round(float(pagerank.get(node, 0.0)), 6),
            "betweenness_centrality": round(float(betweenness.get(node, 0.0)), 6)
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(by="pagerank", ascending=False).reset_index(drop=True)
    return df


def calculate_graph_summary(
    wallet_graph: nx.MultiDiGraph,
    ip_graph: nx.MultiDiGraph,
    investigation_graph: nx.MultiDiGraph
) -> dict:
    """
    Calculate summary statistics across all graphs.

    Returns:
        dict: Summary statistics dictionary.
    """
    # Count node types in investigation_graph
    node_type_counts = {"wallet": 0, "transaction": 0, "ip": 0, "entity": 0}
    for _, data in investigation_graph.nodes(data=True):
        ntype = data.get("node_type", "other")
        if ntype in node_type_counts:
            node_type_counts[ntype] += 1

    try:
        num_components = nx.number_weakly_connected_components(investigation_graph)
    except Exception:
        num_components = 0

    summary = {
        "wallet_graph": {
            "nodes": wallet_graph.number_of_nodes(),
            "edges": wallet_graph.number_of_edges()
        },
        "ip_graph": {
            "nodes": ip_graph.number_of_nodes(),
            "edges": ip_graph.number_of_edges()
        },
        "investigation_graph": {
            "total_nodes": investigation_graph.number_of_nodes(),
            "total_edges": investigation_graph.number_of_edges(),
            "wallet_nodes": node_type_counts["wallet"],
            "transaction_nodes": node_type_counts["transaction"],
            "ip_nodes": node_type_counts["ip"],
            "entity_nodes": node_type_counts["entity"],
            "number_of_connected_components": num_components
        }
    }
    return summary
