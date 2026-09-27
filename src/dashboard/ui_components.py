import altair as alt
import pandas as pd
import streamlit as st
from src.dashboard.theme import render_kpi_card_html, render_status_badge


def render_kpi_row(summary: dict, tx_count: int, obs_count: int):
    """
    Render 6 KPI cards dynamically loaded from existing processed datasets.
    """
    inv_stats = summary.get("investigation_graph", {})
    wallet_stats = summary.get("wallet_graph", {})
    ip_stats = summary.get("ip_graph", {})

    total_tx = tx_count if tx_count > 0 else inv_stats.get("transaction_nodes", 510)
    total_obs = obs_count if obs_count > 0 else ip_stats.get("edges", 1497)
    total_wallets = wallet_stats.get("nodes", 100)
    total_ips = ip_stats.get("nodes", 50)
    total_entities = inv_stats.get("entity_nodes", 20)
    total_nodes = inv_stats.get("total_nodes", 680)

    cols = st.columns(6)

    kpis = [
        ("Blockchain Txs", f"{total_tx:,}", "Validated transactions", "🔗"),
        ("Network Obs.", f"{total_obs:,}", "P2P propagation events", "📡"),
        ("Wallets", f"{total_wallets:,}", "Tracked wallet nodes", "💼"),
        ("IP Nodes", f"{total_ips:,}", "Observed network nodes", "🌐"),
        ("Entities", f"{total_entities:,}", "Mapped synthetic entities", "🏛️"),
        ("Graph Nodes", f"{total_nodes:,}", "Investigation graph nodes", "🕸️")
    ]

    for col, (label, val, desc, icon) in zip(cols, kpis):
        with col:
            st.markdown(render_kpi_card_html(label, val, desc, icon), unsafe_allow_html=True)


def render_activity_chart(df: pd.DataFrame, title: str, subtitle: str, color_hex: str = "#bcf234"):
    """
    Render a modern dark-themed time-series area chart using Altair.
    """
    st.markdown(f"""
    <div style="margin-bottom: 8px;">
        <div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">{title}</div>
        <div style="font-size: 0.78rem; color: #94a3b8;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty or "timestamp" not in df.columns or "count" not in df.columns:
        st.info("Activity data unavailable.")
        return

    # Altair dark gradient area chart
    chart = alt.Chart(df).mark_area(
        interpolate="monotone",
        line={"color": color_hex, "width": 2},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color=color_hex, offset=0),
                alt.GradientStop(color="rgba(10, 13, 20, 0.05)", offset=1)
            ],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X(
            "timestamp:T",
            axis=alt.Axis(
                title=None,
                format="%b %d, %H:%M",
                labelColor="#64748b",
                tickColor="#1f2638",
                domainColor="#1f2638",
                gridColor="#141824",
                labelFontSize=10
            )
        ),
        y=alt.Y(
            "count:Q",
            axis=alt.Axis(
                title=None,
                labelColor="#64748b",
                tickColor="#1f2638",
                domainColor="#1f2638",
                gridColor="#141824",
                labelFontSize=10
            )
        ),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Time", format="%Y-%m-%d %H:%M"),
            alt.Tooltip("count:Q", title="Events")
        ]
    ).properties(
        height=190,
        background="transparent"
    ).configure_view(
        strokeWidth=0
    )

    st.altair_chart(chart, use_container_width=True)


def render_graph_legend():
    """
    Render a visually appealing, compact cybersecurity legend for node types and relationship flows.
    """
    st.markdown("""
    <div style="background-color: #131722; padding: 12px 16px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #1f2638; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
        <span style="color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Node Palette:</span>
        <span style="color: #a855f7; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">&#x2B22; Entity</span>
        <span style="color: #38bdf8; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">&#x25CF; Wallet</span>
        <span style="color: #fb923c; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">&#x25C6; Transaction</span>
        <span style="color: #22c55e; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">&#x25A0; IP Node</span>
      </div>
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Flows:</span>
        <span style="color: #94a3b8; font-size: 11px;">Entity &rarr; Wallet <code style='color:#a855f7; background: rgba(168,85,247,0.1); padding: 2px 4px; border-radius: 4px;'>owns</code></span>
        <span style="color: #94a3b8; font-size: 11px;">Wallet &rarr; TX <code style='color:#38bdf8; background: rgba(56,189,248,0.1); padding: 2px 4px; border-radius: 4px;'>input_to</code></span>
        <span style="color: #94a3b8; font-size: 11px;">TX &rarr; Wallet <code style='color:#fb923c; background: rgba(251,146,60,0.1); padding: 2px 4px; border-radius: 4px;'>output_to</code></span>
        <span style="color: #94a3b8; font-size: 11px;">IP &harr; TX <code style='color:#22c55e; background: rgba(34,197,94,0.1); padding: 2px 4px; border-radius: 4px;'>observed</code></span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_node_intelligence_panel(intel: dict):
    """
    Render an analyst-grade investigation panel for the selected node.
    """
    if not intel.get("found", False):
        st.markdown("""
        <div class="cg-inspector-panel">
            <div class="cg-card-title">Node Intelligence</div>
            <p style="color: #64748b; font-size: 0.85rem;">Select a node in the graph to inspect structural signals.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    ntype = intel.get("node_type", "unknown").capitalize()
    node_id = intel.get("node_id", "")
    metrics = intel.get("metrics", {})
    signals = intel.get("signals", [])

    # Badge class per node type
    badge_variant = "lime"
    if ntype.lower() == "wallet":
        badge_variant = "blue"
    elif ntype.lower() == "transaction":
        badge_variant = "amber"
    elif ntype.lower() == "entity":
        badge_variant = "purple"
    elif ntype.lower() == "ip":
        badge_variant = "lime"

    badge_html = render_status_badge(f"● {ntype.upper()}", badge_variant)

    # Render header & metrics
    metric_cells = "".join([
        f"""
        <div class="cg-metric-cell">
            <div class="cg-metric-cell-label">{k}</div>
            <div class="cg-metric-cell-val">{v}</div>
        </div>
        """ for k, v in metrics.items()
    ])

    signals_html = "".join([
        f'<div class="cg-signal-item"><span>⚡</span><span>{sig}</span></div>'
        for sig in signals
    ])

    st.markdown(f"""
    <div class="cg-inspector-panel">
        <div class="cg-inspector-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; font-weight: 700;">Node Intelligence</span>
                {badge_html}
            </div>
            <div class="cg-node-id-display">{node_id}</div>
        </div>

        <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700; margin-bottom: 8px;">Structural Metrics</div>
        <div class="cg-metric-grid">
            {metric_cells}
        </div>

        <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700; margin-bottom: 8px;">Graph Signals</div>
        <div style="margin-bottom: 14px;">
            {signals_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Connected Neighbors Breakdown in collapsible sections
    entities = intel.get("connected_entities", [])
    wallets = intel.get("connected_wallets", [])
    txs = intel.get("connected_txs", [])
    ips = intel.get("connected_ips", [])

    with st.expander(f"🔗 Connected Topology ({intel.get('total_neighbors', 0)} links)", expanded=True):
        if entities:
            st.markdown(f"**Entities ({len(entities)}):**")
            st.write(", ".join([f"`{e}`" for e in entities[:8]]))
        if wallets:
            st.markdown(f"**Wallets ({len(wallets)}):**")
            st.write(", ".join([f"`{w}`" for w in wallets[:8]]) + ("..." if len(wallets) > 8 else ""))
        if txs:
            st.markdown(f"**Transactions ({len(txs)}):**")
            st.write(", ".join([f"`{t}`" for t in txs[:6]]) + ("..." if len(txs) > 6 else ""))
        if ips:
            st.markdown(f"**Correlated IPs ({len(ips)}):**")
            st.write(", ".join([f"`{ip}`" for ip in ips[:6]]) + ("..." if len(ips) > 6 else ""))


def render_graph_summary_cards(summary: dict):
    """
    Render the 3 Graph Intelligence overview cards with navigation trigger.
    """
    wallet_stats = summary.get("wallet_graph", {})
    ip_stats = summary.get("ip_graph", {})
    inv_stats = summary.get("investigation_graph", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="cg-graph-intel-card">
            <div class="cg-graph-icon-box" style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25);">
                💼
            </div>
            <div>
                <div style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">Wallet Transaction Graph</div>
                <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">
                    <b style="color:#f1f5f9;">{wallet_stats.get('nodes', 100)}</b> Nodes &nbsp;·&nbsp; 
                    <b style="color:#f1f5f9;">{wallet_stats.get('edges', 510)}</b> Edges
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="cg-graph-intel-card">
            <div class="cg-graph-icon-box" style="background: rgba(34, 197, 94, 0.12); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.25);">
                🌐
            </div>
            <div>
                <div style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">IP Communication Graph</div>
                <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">
                    <b style="color:#f1f5f9;">{ip_stats.get('nodes', 50)}</b> Nodes &nbsp;·&nbsp; 
                    <b style="color:#f1f5f9;">{ip_stats.get('edges', 1497):,}</b> Edges
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="cg-graph-intel-card">
            <div class="cg-graph-icon-box" style="background: rgba(168, 85, 247, 0.12); color: #a855f7; border: 1px solid rgba(168, 85, 247, 0.25);">
                🕸️
            </div>
            <div>
                <div style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">Heterogeneous Investigation Graph</div>
                <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">
                    <b style="color:#f1f5f9;">{inv_stats.get('total_nodes', 680)}</b> Nodes &nbsp;·&nbsp; 
                    <b style="color:#f1f5f9;">{inv_stats.get('total_edges', 4114):,}</b> Edges
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_selected_node_inspector(node_id: str, node_data: dict, wallet_metrics_map: dict = None, ip_metrics_map: dict = None):
    """
    Backward-compatible alias for legacy node inspection.
    """
    ntype = node_data.get("node_type", "unknown").capitalize()
    raw_label = node_data.get("label", node_id)

    st.markdown(f"### 🔍 Selected Node Inspector: `{node_id}`")

    if ntype.lower() == "wallet":
        wallet_id = node_data.get("wallet_id", raw_label)
        w_meta = wallet_metrics_map.get(wallet_id, {}) if wallet_metrics_map else {}
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Node Type", "Wallet")
        c2.metric("Wallet ID", wallet_id)
        c3.metric("PageRank", f"{w_meta.get('pagerank', 'N/A')}")
        c4.metric("In-Degree", f"{w_meta.get('in_degree', 0)}")
        c5.metric("Out-Degree", f"{w_meta.get('out_degree', 0)}")
    elif ntype.lower() == "transaction":
        txid = node_data.get("txid", raw_label)
        amount = node_data.get("amount", "N/A")
        fee = node_data.get("fee", "N/A")
        c1, c2, c3 = st.columns(3)
        c1.metric("Node Type", "Transaction")
        c2.metric("TXID", txid)
        c3.metric("Amount", f"{amount} BTC" if amount != "N/A" else "N/A")
    elif ntype.lower() == "ip":
        ip_addr = node_data.get("ip_address", raw_label)
        ip_meta = ip_metrics_map.get(ip_addr, {}) if ip_metrics_map else {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Node Type", "IP Address")
        c2.metric("IP", ip_addr)
        c3.metric("PageRank", f"{ip_meta.get('pagerank', 'N/A')}")
    else:
        st.json(node_data)

