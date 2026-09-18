import os
import tempfile
import networkx as nx
from pyvis.network import Network


# Visual Styling Mappings for Node Types
NODE_COLOR_MAP = {
    "entity": "#9b59b6",       # Purple
    "wallet": "#3498db",       # Blue
    "transaction": "#e67e22",  # Orange
    "ip": "#2ecc71",           # Green
    "other": "#95a5a6"         # Gray
}

NODE_SHAPE_MAP = {
    "entity": "hexagon",
    "wallet": "dot",
    "transaction": "diamond",
    "ip": "square",
    "other": "dot"
}


def extract_neighborhood_subgraph(
    G: nx.MultiDiGraph,
    target_node: str,
    depth: int = 1,
    max_nodes: int = 60
) -> tuple[nx.MultiDiGraph, bool, int, int, set]:
    """
    Extract a prioritized neighborhood subgraph around a target node.

    Priority:
        1. Target node
        2. Direct 1-hop neighbors (predecessors & successors)
        3. High-degree 2-hop neighbors

    Args:
        G (nx.MultiDiGraph): Full investigation or component graph.
        target_node (str): Center node identifier.
        depth (int): Neighborhood hop depth (1 or 2).
        max_nodes (int): Maximum nodes to include in visualized subgraph.

    Returns:
        tuple: (subgraph, is_truncated, total_found, total_shown, direct_neighbors)
    """
    if target_node not in G:
        return nx.MultiDiGraph(), False, 0, 0, set()

    # 1. Direct 1-hop neighbors
    direct_neighbors = set(G.successors(target_node)) | set(G.predecessors(target_node))
    hop1_nodes = set([target_node]) | direct_neighbors

    if depth <= 1:
        total_found = len(hop1_nodes)
        if len(hop1_nodes) > max_nodes:
            # Keep target + top max_nodes-1 direct neighbors
            sorted_hop1 = sorted(
                list(direct_neighbors),
                key=lambda n: G.degree(n),
                reverse=True
            )
            selected_nodes = set([target_node]) | set(sorted_hop1[:max_nodes - 1])
            subgraph = G.subgraph(selected_nodes).copy()
            return subgraph, True, total_found, len(selected_nodes), direct_neighbors
        else:
            subgraph = G.subgraph(hop1_nodes).copy()
            return subgraph, False, total_found, total_found, direct_neighbors

    # 2. 2-hop neighbors
    hop2_neighbors = set()
    for n in direct_neighbors:
        n_neighbors = set(G.successors(n)) | set(G.predecessors(n))
        hop2_neighbors.update(n_neighbors)

    # Exclude already captured hop1 nodes
    hop2_only = hop2_neighbors - hop1_nodes
    all_found_nodes = hop1_nodes | hop2_only
    total_found = len(all_found_nodes)

    if total_found <= max_nodes:
        subgraph = G.subgraph(all_found_nodes).copy()
        return subgraph, False, total_found, total_found, direct_neighbors

    # Truncation needed: prioritize target + all hop1 + top degree hop2
    remaining_slots = max(0, max_nodes - len(hop1_nodes))
    sorted_hop2 = sorted(
        list(hop2_only),
        key=lambda n: G.degree(n),
        reverse=True
    )
    selected_hop2 = set(sorted_hop2[:remaining_slots])
    selected_nodes = hop1_nodes | selected_hop2
    subgraph = G.subgraph(selected_nodes).copy()

    return subgraph, True, total_found, len(selected_nodes), direct_neighbors


def format_node_tooltip(
    node_id: str,
    node_data: dict,
    wallet_metrics_map: dict = None,
    ip_metrics_map: dict = None
) -> str:
    """
    Format a clean plain-text multiline tooltip for a graph node based on its type.

    Args:
        node_id (str): Prefixed or raw node identifier.
        node_data (dict): Attributes dictionary from NetworkX node.
        wallet_metrics_map (dict, optional): Metrics lookup for wallets.
        ip_metrics_map (dict, optional): Metrics lookup for IPs.

    Returns:
        str: Clean plain-text multiline tooltip.
    """
    ntype = node_data.get("node_type", "unknown").lower()
    raw_label = node_data.get("label", node_id)

    lines = []

    if ntype == "entity":
        entity_id = node_data.get("entity_id", raw_label)
        lines.append("Entity Node")
        lines.append(f"Entity ID: {entity_id}")

    elif ntype == "wallet":
        wallet_id = node_data.get("wallet_id", raw_label)
        lines.append("Wallet Node")
        lines.append(f"Wallet ID: {wallet_id}")
        if wallet_metrics_map and wallet_id in wallet_metrics_map:
            w_meta = wallet_metrics_map[wallet_id]
            lines.append(f"PageRank: {w_meta.get('pagerank', 'N/A')}")
            lines.append(f"Betweenness: {w_meta.get('betweenness_centrality', 'N/A')}")
            lines.append(f"Degree (In/Out): {w_meta.get('in_degree', 0)} / {w_meta.get('out_degree', 0)}")

    elif ntype == "transaction":
        txid = node_data.get("txid", raw_label)
        amount = node_data.get("amount", "N/A")
        fee = node_data.get("fee", "N/A")
        timestamp = node_data.get("timestamp", "N/A")
        pattern = node_data.get("pattern_label", "normal")
        script = node_data.get("script_type", "N/A")

        lines.append("Transaction Node")
        lines.append(f"TXID: {txid}")
        lines.append(f"Amount: {amount} BTC")
        lines.append(f"Fee: {fee} BTC")
        lines.append(f"Pattern Label: {pattern}")
        lines.append(f"Script Type: {script}")
        lines.append(f"Timestamp: {timestamp}")

    elif ntype == "ip":
        ip_addr = node_data.get("ip_address", raw_label)
        entity_meta = node_data.get("entity_id", "unmapped")
        node_role = node_data.get("node_type_meta", "unknown")

        lines.append("IP Address Node")
        lines.append(f"IP Address: {ip_addr}")
        lines.append(f"Simulated Role: {node_role}")
        lines.append(f"Entity Association: {entity_meta}")
        if ip_metrics_map and ip_addr in ip_metrics_map:
            ip_meta = ip_metrics_map[ip_addr]
            lines.append(f"PageRank: {ip_meta.get('pagerank', 'N/A')}")
            lines.append(f"Degree (In/Out): {ip_meta.get('in_degree', 0)} / {ip_meta.get('out_degree', 0)}")

    else:
        lines.append(f"Node: {node_id}")
        for k, v in node_data.items():
            if k not in ["label", "node_type"]:
                lines.append(f"{k}: {v}")

    return "\n".join(lines)


def format_edge_tooltip(u: str, v: str, edge_data: dict) -> str:
    """
    Format a clean plain-text multiline hover tooltip for a graph edge.

    Args:
        u (str): Source node identifier.
        v (str): Destination node identifier.
        edge_data (dict): Edge attribute dictionary.

    Returns:
        str: Clean plain-text multiline edge tooltip.
    """
    rel = edge_data.get("relationship", edge_data.get("pattern_label", "connected_to"))
    txid = edge_data.get("txid", "")
    amount = edge_data.get("amount", "")
    fee = edge_data.get("fee", "")
    delay = edge_data.get("observation_delay_ms", "")
    src_port = edge_data.get("src_port", "")
    dst_port = edge_data.get("dst_port", "")

    lines = [f"Relationship: {rel}"]

    if txid:
        lines.append(f"Transaction: {txid}")
    if amount:
        lines.append(f"Amount: {amount} BTC")
    if fee:
        lines.append(f"Fee: {fee} BTC")
    if src_port and dst_port:
        lines.append(f"Ports: {src_port} -> {dst_port}")
    if delay:
        lines.append(f"Obs. Delay: {delay} ms")

    lines.append(f"Direction: {u} -> {v}")
    return "\n".join(lines)


def build_pyvis_network(
    subgraph: nx.MultiDiGraph,
    target_node: str,
    direct_neighbors: set,
    show_all_labels: bool = False,
    show_edge_labels: bool = False,
    enable_physics: bool = True,
    wallet_metrics_map: dict = None,
    ip_metrics_map: dict = None
) -> str:
    """
    Build and render an interactive PyVis graph HTML string with smart labels and tooltips.

    Args:
        subgraph (nx.MultiDiGraph): Subgraph to visualize.
        target_node (str): Center target node.
        direct_neighbors (set): Set of 1-hop neighbor node IDs.
        show_all_labels (bool): Force show all labels regardless of graph size.
        show_edge_labels (bool): Display static text on edges.
        enable_physics (bool): Enable force-directed physics simulation.
        wallet_metrics_map (dict, optional): Wallet metrics mapping.
        ip_metrics_map (dict, optional): IP metrics mapping.

    Returns:
        str: HTML representation of the interactive PyVis graph.
    """
    net = Network(
        height="640px",
        width="100%",
        directed=True,
        bgcolor="#181818",
        font_color="#ffffff"
    )

    num_nodes = subgraph.number_of_nodes()

    # Rule 3: Smart Node Labels
    # If graph <= 30 nodes or show_all_labels is enabled -> show all labels.
    # Otherwise, show labels only for target_node and direct 1-hop neighbors.
    smart_labels_active = (num_nodes > 30) and not show_all_labels

    for n, data in subgraph.nodes(data=True):
        ntype = data.get("node_type", "other").lower()
        color = NODE_COLOR_MAP.get(ntype, "#95a5a6")
        shape = NODE_SHAPE_MAP.get(ntype, "dot")
        raw_label = data.get("label", str(n))

        # Check if label should be visible
        if smart_labels_active:
            if n == target_node or n in direct_neighbors:
                display_label = raw_label
            else:
                display_label = ""  # Hide distant label to prevent clutter
        else:
            display_label = raw_label

        # Visual distinction for selected target node
        is_target = (n == target_node)
        size = 28 if is_target else 16
        border_width = 3 if is_target else 1
        border_color = "#f1c40f" if is_target else color

        tooltip_text = format_node_tooltip(
            node_id=n,
            node_data=data,
            wallet_metrics_map=wallet_metrics_map,
            ip_metrics_map=ip_metrics_map
        )

        net.add_node(
            n,
            label=display_label,
            title=tooltip_text,
            color={
                "background": color,
                "border": border_color,
                "highlight": {"background": "#e74c3c", "border": "#ffffff"}
            },
            shape=shape,
            size=size,
            borderWidth=border_width,
            font={"size": 13, "color": "#ffffff", "face": "Helvetica"}
        )

    # Add Edges (Rule 1: Hide static edge labels by default, show on hover)
    for u, v, data in subgraph.edges(data=True):
        edge_tooltip = format_edge_tooltip(u, v, data)
        static_label = ""
        if show_edge_labels:
            static_label = str(data.get("relationship", data.get("pattern_label", "")))

        net.add_edge(
            u,
            v,
            title=edge_tooltip,
            label=static_label,
            color={"color": "#636e72", "highlight": "#f1c40f"},
            arrows={"to": {"enabled": True, "scaleFactor": 0.6}},
            smooth={"type": "curvedCW", "roundness": 0.15}
        )

    # Graph physics configuration
    if enable_physics:
        net.set_options("""
        {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -4000,
              "centralGravity": 0.3,
              "springLength": 95,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "minVelocity": 0.75,
            "solver": "barnesHut"
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "navigationButtons": true
          }
        }
        """)
    else:
        net.toggle_physics(False)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        tmp_path = tmp.name

    with open(tmp_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return html_code
