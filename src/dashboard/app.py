import json
import os
import sys
import networkx as nx
import pandas as pd
import streamlit as st

# Ensure repository root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.dashboard.graph_visualizer import (
    build_pyvis_network,
    extract_neighborhood_subgraph
)
from src.dashboard.ui_components import (
    render_graph_legend,
    render_selected_node_inspector
)

# Set page configuration
st.set_page_config(
    page_title="Bitcoin AI Monitor - Investigation Graph Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_processed_data():
    """Load cached Phase 4 exported datasets and metrics."""
    proc_dir = os.path.join(project_root, "data/processed")

    summary_path = os.path.join(proc_dir, "graph_summary.json")
    wallet_metrics_path = os.path.join(proc_dir, "wallet_graph_metrics.csv")
    ip_metrics_path = os.path.join(proc_dir, "ip_graph_metrics.csv")

    summary = {}
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    wallet_metrics = pd.read_csv(wallet_metrics_path) if os.path.exists(wallet_metrics_path) else pd.DataFrame()
    ip_metrics = pd.read_csv(ip_metrics_path) if os.path.exists(ip_metrics_path) else pd.DataFrame()

    # Pre-build lookup dictionaries for fast tooltip retrieval
    wallet_metrics_map = {}
    if not wallet_metrics.empty:
        for _, r in wallet_metrics.iterrows():
            wallet_metrics_map[str(r["wallet_id"]).strip()] = r.to_dict()

    ip_metrics_map = {}
    if not ip_metrics.empty:
        for _, r in ip_metrics.iterrows():
            ip_metrics_map[str(r["ip_address"]).strip()] = r.to_dict()

    return summary, wallet_metrics, ip_metrics, wallet_metrics_map, ip_metrics_map


@st.cache_resource
def load_graph_object(graph_type="investigation"):
    """Load GraphML graph structure."""
    proc_dir = os.path.join(project_root, "data/processed")
    filename_map = {
        "investigation": "investigation_graph.graphml",
        "wallet": "wallet_graph.graphml",
        "ip": "ip_graph.graphml"
    }

    graph_file = os.path.join(proc_dir, filename_map.get(graph_type, "investigation_graph.graphml"))
    if os.path.exists(graph_file):
        try:
            return nx.read_graphml(graph_file)
        except Exception:
            pass

    # Fallback to rebuilding if GraphML not found
    from src.graph.run_graph_pipeline import run_graph_pipeline
    wallet_g, ip_g, inv_g = run_graph_pipeline()
    if graph_type == "wallet":
        return wallet_g
    elif graph_type == "ip":
        return ip_g
    return inv_g


# ----------------------------------------------------
# MAIN STREAMLIT APPLICATION
# ----------------------------------------------------

def main():
    st.title("AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic")
    st.caption("Phase 4 — Entity–Wallet–Transaction–IP Investigation Graph Explorer")

    summary, wallet_metrics, ip_metrics, wallet_metrics_map, ip_metrics_map = load_processed_data()

    # Sidebar Navigation
    st.sidebar.header("Navigation")
    navigation = st.sidebar.radio(
        "Select View:",
        ["Investigation Graph Explorer", "System Overview", "Graph Metrics Tables", "Graph Architecture"]
    )

    # ----------------------------------------------------
    # VIEW 1: INTERACTIVE INVESTIGATION GRAPH EXPLORER
    # ----------------------------------------------------
    if navigation == "Investigation Graph Explorer":
        st.subheader("🔍 Interactive Investigation Graph Explorer")

        # Sidebar Graph Controls
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Graph Visualization Controls")

        graph_type = st.sidebar.selectbox(
            "Select Graph Type:",
            ["investigation", "wallet", "ip"],
            format_func=lambda x: "Combined Investigation Graph" if x == "investigation" else f"{x.upper()} Graph"
        )
        G = load_graph_object(graph_type)

        if G.number_of_nodes() == 0:
            st.error("Graph contains no nodes. Please run `python src/graph/run_graph_pipeline.py`.")
            return

        all_nodes = sorted(list(G.nodes()))

        # Filter nodes by type in sidebar if investigation graph
        if graph_type == "investigation":
            node_type_filter = st.sidebar.selectbox(
                "Filter Target Node by Type:",
                ["All", "Wallets", "Transactions", "IPs", "Entities"]
            )
            if node_type_filter == "Wallets":
                filtered_nodes = [n for n in all_nodes if n.startswith("wallet:")]
            elif node_type_filter == "Transactions":
                filtered_nodes = [n for n in all_nodes if n.startswith("tx:")]
            elif node_type_filter == "IPs":
                filtered_nodes = [n for n in all_nodes if n.startswith("ip:")]
            elif node_type_filter == "Entities":
                filtered_nodes = [n for n in all_nodes if n.startswith("entity:")]
            else:
                filtered_nodes = all_nodes
        else:
            filtered_nodes = all_nodes

        # Target node selection
        selected_node = st.sidebar.selectbox(
            "Select Target Node to Explore:",
            filtered_nodes or all_nodes,
            index=0
        )

        depth = st.sidebar.slider("Neighborhood Depth (Hops):", min_value=1, max_value=2, value=1)
        max_nodes = st.sidebar.slider("Maximum Subgraph Nodes:", min_value=20, max_value=150, value=60, step=10)

        # Advanced Visual Options
        with st.sidebar.expander("🎨 Advanced Display Options", expanded=False):
            show_all_labels = st.checkbox("Force Show All Labels", value=False, help="Overrides smart label rule (which hides 2-hop labels on graphs > 30 nodes to reduce clutter).")
            show_edge_labels = st.checkbox("Show Static Edge Labels", value=False, help="Display text directly on edge lines (by default relationship info is shown on edge hover).")
            enable_physics = st.checkbox("Enable Physics Layout", value=True, help="Toggle force-directed physics animation.")

        # 1. Extract Neighborhood Subgraph with Capping Protection
        subgraph, is_truncated, total_found, total_shown, direct_neighbors = extract_neighborhood_subgraph(
            G=G,
            target_node=selected_node,
            depth=depth,
            max_nodes=max_nodes
        )

        # Rule 6: Graph Size Protection Warning
        if is_truncated:
            st.warning(
                f"⚠️ **Large neighborhood detected:** {total_found} nodes found at depth {depth}. "
                f"Showing the **top {total_shown} most relevant nodes** (Target + Direct 1-hop neighbors + High-degree nodes) for visual clarity."
            )

        # 2. Render Graph Legend
        render_graph_legend()

        # 3. Render Node Inspector
        node_data = G.nodes.get(selected_node, {})
        render_selected_node_inspector(
            node_id=selected_node,
            node_data=node_data,
            wallet_metrics_map=wallet_metrics_map,
            ip_metrics_map=ip_metrics_map
        )

        # 4. Render PyVis Interactive Network Graph
        st.markdown(f"#### 🌐 Neighborhood Subgraph ({total_shown} Nodes, {subgraph.number_of_edges()} Edges)")
        html_code = build_pyvis_network(
            subgraph=subgraph,
            target_node=selected_node,
            direct_neighbors=direct_neighbors,
            show_all_labels=show_all_labels,
            show_edge_labels=show_edge_labels,
            enable_physics=enable_physics,
            wallet_metrics_map=wallet_metrics_map,
            ip_metrics_map=ip_metrics_map
        )

        st.components.v1.html(html_code, height=650)
        st.caption("💡 **Tip:** Hover over nodes and edges for full relationship and metadata tooltips. Drag nodes to inspect local cluster connectivity.")

    # ----------------------------------------------------
    # VIEW 2: SYSTEM OVERVIEW
    # ----------------------------------------------------
    elif navigation == "System Overview":
        st.subheader("📊 System Overview & Metrics Summary")

        inv_stats = summary.get("investigation_graph", {})
        wallet_stats = summary.get("wallet_graph", {})
        ip_stats = summary.get("ip_graph", {})

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Blockchain Txs", inv_stats.get("transaction_nodes", 510))
        col2.metric("Network Obs.", ip_stats.get("edges", 1497))
        col3.metric("Wallet Nodes", inv_stats.get("wallet_nodes", 100))
        col4.metric("IP Nodes", inv_stats.get("ip_nodes", 50))
        col5.metric("Entity Nodes", inv_stats.get("entity_nodes", 20))
        col6.metric("Total Graph Edges", inv_stats.get("total_edges", 4114))

        st.markdown("---")
        st.write("### Structural Graph Breakdown")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**Wallet Transaction Graph**\n\n- Nodes: {wallet_stats.get('nodes', 100)}\n- Edges: {wallet_stats.get('edges', 510)}")
        with c2:
            st.success(f"**IP Communication Graph**\n\n- Nodes: {ip_stats.get('nodes', 50)}\n- Edges: {ip_stats.get('edges', 1497)}")
        with c3:
            st.warning(f"**Heterogeneous Investigation Graph**\n\n- Total Nodes: {inv_stats.get('total_nodes', 680)}\n- Weakly Connected Components: {inv_stats.get('number_of_connected_components', 1)}")

    # ----------------------------------------------------
    # VIEW 3: GRAPH METRICS TABLES
    # ----------------------------------------------------
    elif navigation == "Graph Metrics Tables":
        st.subheader("📈 Structural Graph Metrics")

        tab1, tab2 = st.tabs(["Wallet Graph Metrics", "IP Graph Metrics"])

        with tab1:
            st.write("### Wallet Structural Metrics (Ranked by PageRank)")
            if not wallet_metrics.empty:
                st.dataframe(wallet_metrics, use_container_width=True)
            else:
                st.info("Wallet metrics file not found.")

        with tab2:
            st.write("### IP Structural Metrics (Ranked by PageRank)")
            if not ip_metrics.empty:
                st.dataframe(ip_metrics, use_container_width=True)
            else:
                st.info("IP metrics file not found.")

    # ----------------------------------------------------
    # VIEW 4: GRAPH ARCHITECTURE & DOCUMENTATION
    # ----------------------------------------------------
    elif navigation == "Graph Architecture":
        st.subheader("📘 Phase 4 Investigation Graph Architecture")

        st.markdown("""
        ```text
        Synthetic Entity Node (entity:entity_001)
              │
              │ owns
              ▼
        Input Wallet Node (wallet:wallet_001)
              │
              │ input_to
              ▼
        Transaction Node (tx:TX_000001)
              │                     ▲
              │ output_to           │ observed_source / observed_destination
              ▼                     │
        Output Wallet Node (wallet:wallet_050) ── IP Node (ip:104.144.51.184)
        ```

        ### Visualization Enhancements:
        1. **Hidden Edge Labels by Default:** Relationship types and metadata (`owns`, `input_to`, `output_to`, `observed_source`, `delay_ms`) are displayed via hover tooltips instead of static text clutter.
        2. **Distinct Node Shapes & Colors:**
           - **Entity:** Hexagon (Purple `#9b59b6`)
           - **Wallet:** Circle (Blue `#3498db`)
           - **Transaction:** Diamond (Orange `#e67e22`)
           - **IP Address:** Square (Green `#2ecc71`)
        3. **Smart Label Visibility:** Graphs with > 30 nodes only display labels for the target node and direct 1-hop neighbors, keeping 2-hop clusters readable without text overlap.
        4. **Graph Size Protection:** Warns users on large neighborhoods and intelligently prioritizes displaying target, 1-hop, and high-centrality nodes.
        """)


if __name__ == "__main__":
    main()
