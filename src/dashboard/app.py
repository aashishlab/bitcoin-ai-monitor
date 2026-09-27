import os
import sys
import pandas as pd
import streamlit as st

# Ensure repository root is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Invalidate cached submodules on hot-reload to prevent stale imports
for _mod in ["src.dashboard.theme", "src.dashboard.data_loader", "src.dashboard.graph_visualizer", "src.dashboard.ui_components"]:
    if _mod in sys.modules:
        del sys.modules[_mod]

from src.dashboard.theme import (
    inject_theme,
    render_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_status_badge
)
from src.dashboard.data_loader import (
    load_summary_and_metrics,
    load_graph_object,
    get_hourly_activity_data,
    get_node_intelligence_data
)
from src.dashboard.graph_visualizer import (
    build_pyvis_network,
    extract_neighborhood_subgraph
)
from src.dashboard.ui_components import (
    render_kpi_row,
    render_activity_chart,
    render_graph_legend,
    render_node_intelligence_panel,
    render_graph_summary_cards
)

# Page configuration
st.set_page_config(
    page_title="CryptoGuard — Bitcoin Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom dark theme stylesheet
inject_theme()


def init_session_state():
    """Initialize session state for navigation and target node tracking."""
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = "Overview"
    if "target_node_override" not in st.session_state:
        st.session_state["target_node_override"] = None


def main():
    init_session_state()

    # Load all processed datasets dynamically (cached)
    summary, wallet_metrics, ip_metrics, tx_features, corr_events, wallet_metrics_map, ip_metrics_map = load_summary_and_metrics()

    # Sidebar
    render_sidebar_branding()

    nav_options = [
        "Overview",
        "Investigation",
        "Transactions",
        "Network",
        "Graph Intelligence",
        "System"
    ]

    # Handle navigation state sync
    default_idx = 0
    if st.session_state["nav_selection"] in nav_options:
        default_idx = nav_options.index(st.session_state["nav_selection"])

    selected_nav = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=default_idx,
        format_func=lambda x: {
            "Overview": "📊  Overview",
            "Investigation": "🔍  Investigation",
            "Transactions": "💸  Transactions",
            "Network": "🌐  Network",
            "Graph Intelligence": "📈  Graph Intelligence",
            "System": "⚙️  System"
        }.get(x, x)
    )

    # Update session state if user clicked sidebar radio
    st.session_state["nav_selection"] = selected_nav

    render_sidebar_footer()

    # ----------------------------------------------------
    # VIEW 1: OVERVIEW DASHBOARD
    # ----------------------------------------------------
    if selected_nav == "Overview":
        render_header(
            title="Bitcoin Intelligence Overview",
            subtitle="Blockchain + P2P network investigation workspace",
            badge_text="OFFLINE INVESTIGATION PLATFORM",
            badge_type="lime"
        )

        # 1. KPI Cards (Dynamic)
        render_kpi_row(
            summary=summary,
            tx_count=len(tx_features),
            obs_count=len(corr_events)
        )

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 2. Charts (Two-Column Layout)
        tx_hourly, obs_hourly = get_hourly_activity_data(tx_features, corr_events)

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            render_activity_chart(
                df=tx_hourly,
                title="Transaction Activity",
                subtitle="Aggregated on-chain transaction volume over time",
                color_hex="#bcf234"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_col2:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            render_activity_chart(
                df=obs_hourly,
                title="Network Activity",
                subtitle="P2P propagation event telemetry timestamps",
                color_hex="#38bdf8"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 3. Investigation Activity Panel
        st.markdown("""
        <div class="cg-card" style="margin-bottom: 20px;">
            <div class="cg-card-title">
                <span>Recent Investigation Activity</span>
                <span class="cg-badge cg-badge-slate">Synchronized On-Chain + P2P Telemetry</span>
            </div>
            <div class="cg-card-subtitle">
                Transactions observed across P2P propagation nodes with pattern classification
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not tx_features.empty:
            display_cols = [
                "txid", "timestamp", "input_wallet", "output_wallet",
                "amount", "fee", "pattern_label", "network_observation_count"
            ]
            sample_df = tx_features[display_cols].head(12).copy()
            sample_df.rename(columns={
                "txid": "TXID",
                "timestamp": "Timestamp",
                "input_wallet": "Input Wallet",
                "output_wallet": "Output Wallet",
                "amount": "Amount (BTC)",
                "fee": "Fee (BTC)",
                "pattern_label": "Pattern",
                "network_observation_count": "Network Obs."
            }, inplace=True)

            st.dataframe(
                sample_df,
                use_container_width=True,
                height=260
            )

        # Quick pivot to investigate any transaction
        piv_c1, piv_c2 = st.columns([3, 1])
        with piv_c1:
            inspect_tx = st.selectbox(
                "Quick Pivot: Select transaction to explore in investigation graph",
                options=tx_features["txid"].head(25).tolist() if not tx_features.empty else []
            )
        with piv_c2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Investigate in Graph →", key="quick_pivot_btn", type="primary"):
                st.session_state["target_node_override"] = f"tx:{inspect_tx}"
                st.session_state["nav_selection"] = "Investigation"
                st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # 4. Graph Intelligence Section
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 12px;">
            <div>
                <span style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">Graph Intelligence</span>
                <span style="font-size: 0.8rem; color: #94a3b8; margin-left: 10px;">Pre-computed structural layers</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_graph_summary_cards(summary)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Open Investigation Graph Explorer →", key="open_explorer_btn", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Investigation"
            st.rerun()

    # ----------------------------------------------------
    # VIEW 2: INVESTIGATION GRAPH EXPLORER
    # ----------------------------------------------------
    elif selected_nav == "Investigation":
        render_header(
            title="Investigation Graph",
            subtitle="Explore relationships between entities, wallets, transactions and network nodes",
            badge_text="INTERACTIVE INVESTIGATOR",
            badge_type="lime"
        )

        # Compact Top Control Bar
        st.markdown('<div class="cg-card" style="padding: 14px 18px; margin-bottom: 16px;">', unsafe_allow_html=True)
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns([1.5, 1.2, 2.5, 1.2, 1.2])

        with ctrl_col1:
            graph_type = st.selectbox(
                "Graph Scope:",
                ["investigation", "wallet", "ip"],
                format_func=lambda x: "Combined Investigation" if x == "investigation" else f"{x.upper()} Graph"
            )

        G = load_graph_object(graph_type)
        if G.number_of_nodes() == 0:
            st.error("Graph contains no nodes. Please verify data pipeline.")
            return

        all_nodes = sorted(list(G.nodes()))

        with ctrl_col2:
            if graph_type == "investigation":
                node_type_filter = st.selectbox(
                    "Node Filter:",
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

        # Handle override target node from session state
        initial_index = 0
        if st.session_state.get("target_node_override"):
            override_node = st.session_state["target_node_override"]
            if override_node in filtered_nodes:
                initial_index = filtered_nodes.index(override_node)
            st.session_state["target_node_override"] = None  # Consume override

        with ctrl_col3:
            selected_node = st.selectbox(
                "Target Node:",
                filtered_nodes or all_nodes,
                index=initial_index
            )

        with ctrl_col4:
            depth = st.slider("Neighborhood Hops:", min_value=1, max_value=2, value=1)

        with ctrl_col5:
            max_nodes = st.slider("Max Nodes:", min_value=20, max_value=150, value=60, step=10)

        # Advanced visual toggles
        with st.expander("Display & Physics Options", expanded=False):
            adv_c1, adv_c2, adv_c3 = st.columns(3)
            with adv_c1:
                enable_physics = st.checkbox("Enable Physics Simulation", value=True)
            with adv_c2:
                show_edge_labels = st.checkbox("Show Static Edge Labels", value=False)
            with adv_c3:
                show_all_labels = st.checkbox("Force Show All Labels", value=False)

        st.markdown('</div>', unsafe_allow_html=True)

        # 1. Extract Neighborhood Subgraph
        subgraph, is_truncated, total_found, total_shown, direct_neighbors = extract_neighborhood_subgraph(
            G=G,
            target_node=selected_node,
            depth=depth,
            max_nodes=max_nodes
        )

        if is_truncated:
            st.warning(
                f"⚠️ Large neighborhood: {total_found} nodes detected at depth {depth}. "
                f"Displaying top {total_shown} most relevant nodes (Target + 1-hop + High-degree nodes)."
            )

        # 2. Main Two-Column Investigation Layout
        graph_col, inspector_col = st.columns([2.3, 1.1])

        with graph_col:
            # Subgraph status header
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.92rem; font-weight: 600; color: #ffffff;">
                    Interactive Topology Subgraph
                </span>
                <span class="cg-badge cg-badge-lime">
                    {total_shown} Nodes · {subgraph.number_of_edges()} Edges
                </span>
            </div>
            """, unsafe_allow_html=True)

            # PyVis Interactive Network Graph
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

            st.components.v1.html(html_code, height=640)

            # Graph Legend below visualization
            render_graph_legend()

        with inspector_col:
            # Analyst Node Intelligence Panel
            intel = get_node_intelligence_data(
                G=G,
                node_id=selected_node,
                wallet_metrics_map=wallet_metrics_map,
                ip_metrics_map=ip_metrics_map,
                tx_features_df=tx_features
            )
            render_node_intelligence_panel(intel)

            # Pivot to neighbor action
            neighbors = list(direct_neighbors)
            if neighbors:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="cg-card" style="padding: 12px;">', unsafe_allow_html=True)
                st.markdown("<span style='font-size: 0.76rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;'>Pivot Center:</span>", unsafe_allow_html=True)
                pivot_choice = st.selectbox("Select connected neighbor to center graph:", sorted(neighbors))
                if st.button("Pivot to Selected Neighbor ➔", use_container_width=True):
                    st.session_state["target_node_override"] = pivot_choice
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 3: TRANSACTIONS
    # ----------------------------------------------------
    elif selected_nav == "Transactions":
        render_header(
            title="Transaction Intelligence",
            subtitle="Cryptographic on-chain ledger records correlated with P2P network telemetry",
            badge_text="510 ON-CHAIN TRANSACTIONS",
            badge_type="amber"
        )

        if tx_features.empty:
            st.info("No transaction data available.")
            return

        # Transaction Filter Bar
        st.markdown('<div class="cg-card" style="padding: 14px 18px; margin-bottom: 16px;">', unsafe_allow_html=True)
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.8, 1.2, 1.2, 2.0])

        with f_col1:
            search_query = st.text_input("Search TXID or Wallet ID:", placeholder="e.g. TX_000001 or wallet_082").strip()

        with f_col2:
            patterns = ["All"] + sorted(tx_features["pattern_label"].dropna().unique().tolist())
            selected_pattern = st.selectbox("Pattern Filter:", patterns)

        with f_col3:
            scripts = ["All"] + sorted(tx_features["script_type"].dropna().unique().tolist())
            selected_script = st.selectbox("Script Type:", scripts)

        with f_col4:
            min_amt = float(tx_features["amount"].min())
            max_amt = float(tx_features["amount"].max())
            amt_range = st.slider("Amount Filter (BTC):", min_value=min_amt, max_value=max_amt, value=(min_amt, max_amt))

        st.markdown('</div>', unsafe_allow_html=True)

        # Apply Filters
        filtered_tx = tx_features.copy()
        if search_query:
            filtered_tx = filtered_tx[
                filtered_tx["txid"].str.contains(search_query, case=False, na=False) |
                filtered_tx["input_wallet"].str.contains(search_query, case=False, na=False) |
                filtered_tx["output_wallet"].str.contains(search_query, case=False, na=False)
            ]
        if selected_pattern != "All":
            filtered_tx = filtered_tx[filtered_tx["pattern_label"] == selected_pattern]
        if selected_script != "All":
            filtered_tx = filtered_tx[filtered_tx["script_type"] == selected_script]
        filtered_tx = filtered_tx[
            (filtered_tx["amount"] >= amt_range[0]) &
            (filtered_tx["amount"] <= amt_range[1])
        ]

        # Summary Metrics for Filtered Set
        k_c1, k_c2, k_c3, k_c4 = st.columns(4)
        with k_c1:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='cg-kpi-label'>Filtered Txs</div><div class='cg-kpi-value'>{len(filtered_tx)}</div><div class='cg-kpi-desc'>Matching active criteria</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with k_c2:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            tot_vol = filtered_tx["amount"].sum() if not filtered_tx.empty else 0.0
            st.markdown(f"<div class='cg-kpi-label'>Total Volume</div><div class='cg-kpi-value'>{tot_vol:,.2f}</div><div class='cg-kpi-desc'>Bitcoin transacted</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with k_c3:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            avg_obs = filtered_tx["network_observation_count"].mean() if not filtered_tx.empty else 0.0
            st.markdown(f"<div class='cg-kpi-label'>Avg Network Obs</div><div class='cg-kpi-value'>{avg_obs:.1f}</div><div class='cg-kpi-desc'>P2P observations per tx</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with k_c4:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            anom_count = len(filtered_tx[filtered_tx["pattern_label"] != "normal"]) if not filtered_tx.empty else 0
            st.markdown(f"<div class='cg-kpi-label'>Flagged Patterns</div><div class='cg-kpi-value' style='color:#fb923c;'>{anom_count}</div><div class='cg-kpi-desc'>Non-standard classifications</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Polished Transactions Table
        table_cols = [
            "txid", "timestamp", "input_wallet", "output_wallet",
            "amount", "fee", "script_type", "pattern_label",
            "network_observation_count", "avg_observation_delay_ms"
        ]
        render_table = filtered_tx[table_cols].copy()
        render_table.rename(columns={
            "txid": "TXID",
            "timestamp": "Timestamp",
            "input_wallet": "Input Wallet",
            "output_wallet": "Output Wallet",
            "amount": "Amount (BTC)",
            "fee": "Fee (BTC)",
            "script_type": "Script",
            "pattern_label": "Pattern Label",
            "network_observation_count": "Obs. Count",
            "avg_observation_delay_ms": "Avg Delay (ms)"
        }, inplace=True)

        st.dataframe(render_table, use_container_width=True, height=360)

        # Detailed Inspection Expander for Selected Transaction
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        with st.expander("🔍 Deep Telemetry Inspector for Selected Transaction", expanded=False):
            inspect_tx_id = st.selectbox("Choose TXID to inspect cross-layer propagation:", filtered_tx["txid"].tolist())
            if inspect_tx_id:
                corr_sub = corr_events[corr_events["txid"] == inspect_tx_id]
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(f"**Transaction:** `{inspect_tx_id}`")
                    tx_record = filtered_tx[filtered_tx["txid"] == inspect_tx_id].iloc[0]
                    st.write(f"- **Amount:** {tx_record['Amount (BTC)']} BTC")
                    st.write(f"- **Fee:** {tx_record['Fee (BTC)']} BTC")
                    st.write(f"- **Input:** `{tx_record['Input Wallet']}`")
                    st.write(f"- **Output:** `{tx_record['Output Wallet']}`")
                    st.write(f"- **Pattern:** `{tx_record['Pattern Label']}`")
                    if st.button("Explore in Investigation Graph ➔", key=f"inv_tx_{inspect_tx_id}"):
                        st.session_state["target_node_override"] = f"tx:{inspect_tx_id}"
                        st.session_state["nav_selection"] = "Investigation"
                        st.rerun()
                with c2:
                    st.markdown(f"**Correlated P2P Observations ({len(corr_sub)} events):**")
                    if not corr_sub.empty:
                        sub_disp = corr_sub[["timestamp_obs", "src_ip", "dst_ip", "src_port", "dst_port", "observation_delay_ms"]].copy()
                        sub_disp.rename(columns={
                            "timestamp_obs": "Obs Time",
                            "src_ip": "Source IP",
                            "dst_ip": "Destination IP",
                            "src_port": "Src Port",
                            "dst_port": "Dst Port",
                            "observation_delay_ms": "Delay (ms)"
                        }, inplace=True)
                        st.dataframe(sub_disp, use_container_width=True, height=180)

    # ----------------------------------------------------
    # VIEW 4: NETWORK INTELLIGENCE
    # ----------------------------------------------------
    elif selected_nav == "Network":
        render_header(
            title="Network Intelligence",
            subtitle="P2P network observation propagation, relay nodes and structural IP metrics",
            badge_text="50 OBSERVED IP NODES",
            badge_type="lime"
        )

        # Top Network Metrics
        tot_ips = len(ip_metrics) if not ip_metrics.empty else 50
        tot_obs = len(corr_events) if not corr_events.empty else 1497
        uniq_src = corr_events["src_ip"].nunique() if not corr_events.empty else 0
        uniq_dst = corr_events["dst_ip"].nunique() if not corr_events.empty else 0
        avg_delay = corr_events["observation_delay_ms"].mean() if not corr_events.empty else 0.0

        n_col1, n_col2, n_col3, n_col4, n_col5 = st.columns(5)
        with n_col1:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='cg-kpi-label'>Total IP Nodes</div><div class='cg-kpi-value'>{tot_ips}</div><div class='cg-kpi-desc'>Network topology peers</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with n_col2:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='cg-kpi-label'>Network Obs.</div><div class='cg-kpi-value'>{tot_obs:,}</div><div class='cg-kpi-desc'>Captured propagation links</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with n_col3:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='cg-kpi-label'>Unique Source IPs</div><div class='cg-kpi-value'>{uniq_src}</div><div class='cg-kpi-desc'>Relay originating hosts</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with n_col4:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='cg-kpi-label'>Unique Dest IPs</div><div class='cg-kpi-value'>{uniq_dst}</div><div class='cg-kpi-desc'>Observation endpoints</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with n_col5:
            st.markdown('<div class="cg-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='cg-kpi-label'>Avg Delay</div><div class='cg-kpi-value'>{avg_delay:.1f} <span style='font-size: 1rem; color: #8b949e;'>ms</span></div><div class='cg-kpi-desc'>Mean P2P broadcast delay</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # Top Source & Destination IPs
        ip_c1, ip_c2 = st.columns(2)

        with ip_c1:
            st.markdown("""
            <div class="cg-card" style="margin-bottom: 12px;">
                <div class="cg-card-title">Top Relay Source IPs</div>
                <div class="cg-card-subtitle">Nodes originating the highest volume of transaction broadcasts</div>
            </div>
            """, unsafe_allow_html=True)
            if not corr_events.empty:
                top_src = corr_events["src_ip"].value_counts().head(8).reset_index()
                top_src.columns = ["IP Address", "Broadcast Count"]
                st.dataframe(top_src, use_container_width=True, height=240)

        with ip_c2:
            st.markdown("""
            <div class="cg-card" style="margin-bottom: 12px;">
                <div class="cg-card-title">Top Observation Destination IPs</div>
                <div class="cg-card-subtitle">Nodes receiving transaction propagation telemetry</div>
            </div>
            """, unsafe_allow_html=True)
            if not corr_events.empty:
                top_dst = corr_events["dst_ip"].value_counts().head(8).reset_index()
                top_dst.columns = ["IP Address", "Observation Count"]
                st.dataframe(top_dst, use_container_width=True, height=240)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Full IP Graph Metrics Table
        st.markdown("""
        <div class="cg-card" style="margin-bottom: 12px;">
            <div class="cg-card-title">IP Graph Structural Metrics (Ranked by PageRank)</div>
            <div class="cg-card-subtitle">Comprehensive centrality scores calculated across the 50-node P2P communication graph</div>
        </div>
        """, unsafe_allow_html=True)

        if not ip_metrics.empty:
            ip_disp = ip_metrics.copy()
            ip_disp.rename(columns={
                "ip_address": "IP Address",
                "in_degree": "In-Degree",
                "out_degree": "Out-Degree",
                "total_degree": "Total Degree",
                "degree_centrality": "Degree Centrality",
                "pagerank": "PageRank",
                "betweenness_centrality": "Betweenness Centrality"
            }, inplace=True)
            st.dataframe(ip_disp, use_container_width=True, height=320)

    # ----------------------------------------------------
    # VIEW 5: GRAPH INTELLIGENCE & ANALYTICS
    # ----------------------------------------------------
    elif selected_nav == "Graph Intelligence":
        render_header(
            title="Graph Intelligence & Analytics",
            subtitle="Centrality metrics, PageRank prestige, and topological bridge analysis",
            badge_text="TOPOLOGICAL ANALYSIS",
            badge_type="purple"
        )

        # Explanation Cards with Neutral Terminology
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown("""
            <div class="cg-card">
                <div class="cg-card-title" style="color: #38bdf8;">High Connectivity (Degree)</div>
                <div class="cg-card-subtitle">Measures the total volume of direct incoming and outgoing links. Represents high-throughput aggregation hubs.</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown("""
            <div class="cg-card">
                <div class="cg-card-title" style="color: #bcf234;">Structural Importance (PageRank)</div>
                <div class="cg-card-subtitle">Quantifies topological prominence based on the importance of connected neighbors across the complete network.</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown("""
            <div class="cg-card">
                <div class="cg-card-title" style="color: #a855f7;">Bridge Centrality (Betweenness)</div>
                <div class="cg-card-subtitle">Identifies critical intermediary conduits along shortest paths connecting disparate wallet or IP clusters.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs([
            "🏆 Top Connected Wallets",
            "⭐ Top PageRank Wallets",
            "🌉 Top Bridge-like Wallets",
            "🌐 Top Network IP Nodes"
        ])

        with tab1:
            st.markdown("#### Wallets with Highest Direct Connectivity")
            st.caption("Neutral indicator: High degree indicates active transactional hubs or high-frequency relay participants.")
            if not wallet_metrics.empty:
                top_conn = wallet_metrics.sort_values(by="total_degree", ascending=False).head(15)[
                    ["wallet_id", "total_degree", "in_degree", "out_degree", "pagerank", "betweenness_centrality"]
                ].copy()
                top_conn.rename(columns={
                    "wallet_id": "Wallet ID",
                    "total_degree": "Total Degree",
                    "in_degree": "In-Degree",
                    "out_degree": "Out-Degree",
                    "pagerank": "PageRank",
                    "betweenness_centrality": "Betweenness"
                }, inplace=True)
                st.dataframe(top_conn, use_container_width=True)

        with tab2:
            st.markdown("#### Wallets with Highest Structural Importance (PageRank)")
            st.caption("Neutral indicator: Elevated PageRank indicates strong structural prestige in the wallet graph.")
            if not wallet_metrics.empty:
                top_pr = wallet_metrics.sort_values(by="pagerank", ascending=False).head(15)[
                    ["wallet_id", "pagerank", "total_degree", "in_degree", "out_degree", "betweenness_centrality"]
                ].copy()
                top_pr.rename(columns={
                    "wallet_id": "Wallet ID",
                    "pagerank": "PageRank",
                    "total_degree": "Total Degree",
                    "in_degree": "In-Degree",
                    "out_degree": "Out-Degree",
                    "betweenness_centrality": "Betweenness"
                }, inplace=True)
                st.dataframe(top_pr, use_container_width=True)

        with tab3:
            st.markdown("#### Wallets with Highest Bridge Centrality (Betweenness)")
            st.caption("Neutral indicator: High betweenness indicates critical architectural bridges between transaction subgraphs.")
            if not wallet_metrics.empty:
                top_bc = wallet_metrics.sort_values(by="betweenness_centrality", ascending=False).head(15)[
                    ["wallet_id", "betweenness_centrality", "total_degree", "pagerank", "in_degree", "out_degree"]
                ].copy()
                top_bc.rename(columns={
                    "wallet_id": "Wallet ID",
                    "betweenness_centrality": "Betweenness",
                    "total_degree": "Total Degree",
                    "pagerank": "PageRank",
                    "in_degree": "In-Degree",
                    "out_degree": "Out-Degree"
                }, inplace=True)
                st.dataframe(top_bc, use_container_width=True)

        with tab4:
            st.markdown("#### IP Network Nodes with Highest Structural Centrality")
            st.caption("Neutral indicator: High centrality IP nodes act as primary broadcast relays in the P2P overlay.")
            if not ip_metrics.empty:
                top_ips = ip_metrics.sort_values(by="pagerank", ascending=False).head(15)[
                    ["ip_address", "pagerank", "total_degree", "in_degree", "out_degree", "betweenness_centrality"]
                ].copy()
                top_ips.rename(columns={
                    "ip_address": "IP Address",
                    "pagerank": "PageRank",
                    "total_degree": "Total Degree",
                    "in_degree": "In-Degree",
                    "out_degree": "Out-Degree",
                    "betweenness_centrality": "Betweenness"
                }, inplace=True)
                st.dataframe(top_ips, use_container_width=True)

    # ----------------------------------------------------
    # VIEW 6: SYSTEM ARCHITECTURE & VERIFICATION
    # ----------------------------------------------------
    elif selected_nav == "System":
        render_header(
            title="System Architecture & Pipeline",
            subtitle="Offline data processing pipeline lifecycle, graph synthesis, and phase verification",
            badge_text="PHASE 4 COMPLETED",
            badge_type="lime"
        )

        # Pipeline Flow Visualizer
        st.markdown("""
        <div class="cg-card" style="margin-bottom: 20px;">
            <div class="cg-card-title">Completed Offline Intelligence Pipeline</div>
            <div class="cg-card-subtitle">End-to-end data lifecycle from synthetic generation through graph visualization</div>
            
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-top: 14px;">
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 1</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Data Generation</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">510 Txs · 1,497 Obs</div>
                </div>
                <div style="color: #64748b; font-size: 1.2rem;">➔</div>
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 2</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Validation</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">Schema & Hashes</div>
                </div>
                <div style="color: #64748b; font-size: 1.2rem;">➔</div>
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 3</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Cleaning</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">Deduplication</div>
                </div>
                <div style="color: #64748b; font-size: 1.2rem;">➔</div>
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 4</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">TXID Correlation</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">Blockchain + P2P</div>
                </div>
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-top: 14px;">
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 5</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Feature Eng.</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">16 Features</div>
                </div>
                <div style="color: #64748b; font-size: 1.2rem;">➔</div>
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 6</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Graph Synthesis</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">680 Nodes · 4,114 Edges</div>
                </div>
                <div style="color: #64748b; font-size: 1.2rem;">➔</div>
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 7</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Graph Metrics</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">PageRank & Centrality</div>
                </div>
                <div style="color: #64748b; font-size: 1.2rem;">➔</div>
                <div style="background: rgba(188, 242, 52, 0.08); border: 1px solid var(--cg-accent-lime-border); border-radius: 10px; padding: 10px 14px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #bcf234; font-size: 1.1rem; font-weight: 700;">✓ Stage 8</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Investigation UI</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">PyVis & CryptoGuard</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Roadmap & Upcoming Phases
        st.markdown("### 🚀 Project Roadmap & Implementation Status")

        r_col1, r_col2 = st.columns(2)

        with r_col1:
            st.markdown("""
            <div class="cg-card">
                <div style="font-size: 0.95rem; font-weight: 700; color: #ffffff; margin-bottom: 10px;">
                    Completed Modules (Phase 1–4)
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.84rem;">
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">Synthetic Bitcoin transaction generation (510 txs)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">P2P network propagation telemetry (1,497 observations)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">Cross-layer TXID correlation and time-delay matching</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">100-node Wallet Transaction Directed Graph</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">50-node IP Communication Directed Graph</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">680-node Heterogeneous Multi-Type Investigation Graph</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; color: #bcf234;">
                        <span>✓</span> <span style="color: #f1f5f9;">Interactive PyVis neighborhood exploration & capping</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with r_col2:
            st.markdown("""
            <div class="cg-card">
                <div style="font-size: 0.95rem; font-weight: 700; color: #ffffff; margin-bottom: 10px;">
                    Upcoming Capabilities (Phase 5–8 Roadmap)
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.84rem;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="cg-badge cg-badge-amber">Phase 5</span>
                        <span style="color: #cbd5e1;">AI/ML Anomaly Detection (Isolation Forest, GNN) — Coming Next</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="cg-badge cg-badge-amber">Phase 6</span>
                        <span style="color: #cbd5e1;">Multi-Factor Risk Scoring Engine — Coming Next</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="cg-badge cg-badge-purple">Phase 7</span>
                        <span style="color: #cbd5e1;">Entity Clustering & Common-Input Heuristic Expansion — Planned</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="cg-badge cg-badge-slate">Phase 8</span>
                        <span style="color: #cbd5e1;">Offline MaxMind GeoIP & ASN Infrastructure Enrichment — Planned</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Technical Specifications
        st.markdown("""
        <div class="cg-card">
            <div class="cg-card-title">Technical Specifications & Data Verification</div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 10px;">
                <div style="background: rgba(10, 13, 20, 0.5); padding: 10px; border-radius: 8px; border: 1px solid var(--cg-border);">
                    <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 600;">GRAPHML SIZE</div>
                    <div style="font-size: 1.1rem; color: #f1f5f9; font-family: monospace; font-weight: 700;">1.13 MB</div>
                    <div style="font-size: 0.68rem; color: #64748b;">investigation_graph.graphml</div>
                </div>
                <div style="background: rgba(10, 13, 20, 0.5); padding: 10px; border-radius: 8px; border: 1px solid var(--cg-border);">
                    <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 600;">CONNECTED COMPONENTS</div>
                    <div style="font-size: 1.1rem; color: #bcf234; font-family: monospace; font-weight: 700;">1 Component</div>
                    <div style="font-size: 0.68rem; color: #64748b;">Fully connected graph</div>
                </div>
                <div style="background: rgba(10, 13, 20, 0.5); padding: 10px; border-radius: 8px; border: 1px solid var(--cg-border);">
                    <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 600;">GRAPH ENGINE</div>
                    <div style="font-size: 1.1rem; color: #38bdf8; font-family: monospace; font-weight: 700;">NetworkX + PyVis</div>
                    <div style="font-size: 0.68rem; color: #64748b;">MultiDiGraph structure</div>
                </div>
                <div style="background: rgba(10, 13, 20, 0.5); padding: 10px; border-radius: 8px; border: 1px solid var(--cg-border);">
                    <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 600;">DEPLOYMENT MODE</div>
                    <div style="font-size: 1.1rem; color: #22c55e; font-family: monospace; font-weight: 700;">100% Air-Gapped</div>
                    <div style="font-size: 0.68rem; color: #64748b;">Zero internet dependency</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
