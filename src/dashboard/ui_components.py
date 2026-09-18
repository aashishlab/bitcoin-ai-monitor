import streamlit as st


def render_graph_legend():
    """
    Render a visually appealing, non-intrusive legend for node types and relationship flows.
    """
    st.markdown("""
    <div style="background-color: #262730; padding: 14px 18px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #3498db;">
      <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 15px;">
        <div>
          <strong style="color: #ecf0f1; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Node Types:</strong><br>
          <span style="color: #9b59b6; font-size: 14px; margin-right: 12px;">&#x2B22; <b>Entity</b> (Hexagon)</span>
          <span style="color: #3498db; font-size: 14px; margin-right: 12px;">&#x25CF; <b>Wallet</b> (Circle)</span>
          <span style="color: #e67e22; font-size: 14px; margin-right: 12px;">&#x25C6; <b>Transaction</b> (Diamond)</span>
          <span style="color: #2ecc71; font-size: 14px;">&#x25A0; <b>IP Address</b> (Square)</span>
        </div>
        <div>
          <strong style="color: #ecf0f1; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Relationships:</strong><br>
          <span style="color: #bdc3c7; font-size: 12px; margin-right: 10px;">Entity &rarr; Wallet <code style='color:#e056fd'>owns</code></span>
          <span style="color: #bdc3c7; font-size: 12px; margin-right: 10px;">Wallet &rarr; TX <code style='color:#686de0'>input</code></span>
          <span style="color: #bdc3c7; font-size: 12px; margin-right: 10px;">TX &rarr; Wallet <code style='color:#f0932b'>output</code></span>
          <span style="color: #bdc3c7; font-size: 12px;">IP &harr; TX <code style='color:#6ab04c'>network obs</code></span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_selected_node_inspector(
    node_id: str,
    node_data: dict,
    wallet_metrics_map: dict = None,
    ip_metrics_map: dict = None
):
    """
    Render a structured inspector card for the selected graph node.

    Args:
        node_id (str): Selected node identifier.
        node_data (dict): Node attribute dictionary.
        wallet_metrics_map (dict, optional): Wallet metrics mapping.
        ip_metrics_map (dict, optional): IP metrics mapping.
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
        pattern = node_data.get("pattern_label", "normal")
        timestamp = node_data.get("timestamp", "N/A")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Node Type", "Transaction")
        c2.metric("TXID", txid)
        c3.metric("Amount", f"{amount} BTC" if amount != "N/A" else "N/A")
        c4.metric("Fee", f"{fee} BTC" if fee != "N/A" else "N/A")
        c5.metric("Pattern", str(pattern))

        st.caption(f"**Timestamp:** `{timestamp}` | **Script Type:** `{node_data.get('script_type', 'N/A')}`")

    elif ntype.lower() == "ip":
        ip_addr = node_data.get("ip_address", raw_label)
        ip_meta = ip_metrics_map.get(ip_addr, {}) if ip_metrics_map else {}

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Node Type", "IP Address")
        c2.metric("IP", ip_addr)
        c3.metric("Role", str(node_data.get("node_type_meta", "unknown")))
        c4.metric("Entity Assoc.", str(node_data.get("entity_id", "unmapped")))
        c5.metric("PageRank", f"{ip_meta.get('pagerank', 'N/A')}")

    elif ntype.lower() == "entity":
        entity_id = node_data.get("entity_id", raw_label)
        c1, c2 = st.columns(2)
        c1.metric("Node Type", "Synthetic Entity")
        c2.metric("Entity ID", entity_id)

    else:
        st.json(node_data)
