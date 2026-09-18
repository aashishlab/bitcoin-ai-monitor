import networkx as nx
import pandas as pd


def build_investigation_graph(
    blockchain_df: pd.DataFrame,
    network_df: pd.DataFrame,
    entity_wallet_df: pd.DataFrame = None,
    ip_mapping_df: pd.DataFrame = None
) -> nx.MultiDiGraph:
    """
    Build a heterogeneous investigation MultiDiGraph combining Entities, Wallets, Transactions, and IPs.

    Args:
        blockchain_df (pd.DataFrame): Blockchain transactions dataset.
        network_df (pd.DataFrame): Network P2P observations dataset.
        entity_wallet_df (pd.DataFrame, optional): Ground-truth Entity to Wallet mapping.
        ip_mapping_df (pd.DataFrame, optional): Ground-truth IP metadata mapping.

    Returns:
        nx.MultiDiGraph: Heterogeneous multi-directed investigation graph with prefixed node IDs.
    """
    G = nx.MultiDiGraph()

    # 1. Add Entity -> Wallet ownership edges (if ground truth provided)
    if entity_wallet_df is not None and not entity_wallet_df.empty:
        for _, row in entity_wallet_df.iterrows():
            entity_id = str(row["entity_id"]).strip()
            wallet_id = str(row["wallet_id"]).strip()

            entity_node = f"entity:{entity_id}"
            wallet_node = f"wallet:{wallet_id}"

            G.add_node(entity_node, node_type="entity", entity_id=entity_id, label=entity_id)
            G.add_node(wallet_node, node_type="wallet", wallet_id=wallet_id, label=wallet_id)

            G.add_edge(entity_node, wallet_node, relationship="owns")

    # 2. Add IP metadata nodes (if provided)
    ip_meta_map = {}
    if ip_mapping_df is not None and not ip_mapping_df.empty:
        for _, row in ip_mapping_df.iterrows():
            ip_addr = str(row["ip_address"]).strip()
            ip_meta_map[ip_addr] = {
                "entity_id": str(row.get("entity_id", "unmapped")).strip(),
                "node_type_meta": str(row.get("node_type", "unknown")).strip()
            }

    # 3. Add Blockchain Transaction Nodes and Wallet Edges
    if not blockchain_df.empty:
        for _, row in blockchain_df.iterrows():
            txid = str(row["txid"]).strip()
            in_w = str(row["input_wallet"]).strip()
            out_w = str(row["output_wallet"]).strip()

            tx_node = f"tx:{txid}"
            in_w_node = f"wallet:{in_w}"
            out_w_node = f"wallet:{out_w}"

            # Nodes
            G.add_node(
                tx_node,
                node_type="transaction",
                txid=txid,
                label=txid,
                amount=float(row["amount"]),
                fee=float(row["fee"]),
                timestamp=str(row["timestamp"]).strip(),
                script_type=str(row.get("script_type", "")).strip(),
                pattern_label=str(row.get("pattern_label", "")).strip()
            )
            G.add_node(in_w_node, node_type="wallet", wallet_id=in_w, label=in_w)
            G.add_node(out_w_node, node_type="wallet", wallet_id=out_w, label=out_w)

            # Directed Edges
            G.add_edge(in_w_node, tx_node, relationship="input_to", txid=txid, amount=float(row["amount"]))
            G.add_edge(tx_node, out_w_node, relationship="output_to", txid=txid, amount=float(row["amount"]))

    # 4. Add Network Observation Edges (IP -> TX -> IP)
    if not network_df.empty:
        for _, row in network_df.iterrows():
            txid = str(row["txid"]).strip()
            src_ip = str(row["src_ip"]).strip()
            dst_ip = str(row["dst_ip"]).strip()

            tx_node = f"tx:{txid}"
            src_ip_node = f"ip:{src_ip}"
            dst_ip_node = f"ip:{dst_ip}"

            # Add IP nodes if not already present
            src_meta = ip_meta_map.get(src_ip, {})
            dst_meta = ip_meta_map.get(dst_ip, {})

            G.add_node(
                src_ip_node,
                node_type="ip",
                ip_address=src_ip,
                label=src_ip,
                entity_id=src_meta.get("entity_id", "unmapped"),
                node_type_meta=src_meta.get("node_type_meta", "unknown")
            )
            G.add_node(
                dst_ip_node,
                node_type="ip",
                ip_address=dst_ip,
                label=dst_ip,
                entity_id=dst_meta.get("entity_id", "unmapped"),
                node_type_meta=dst_meta.get("node_type_meta", "unknown")
            )

            # Ensure tx node exists
            if tx_node not in G:
                G.add_node(tx_node, node_type="transaction", txid=txid, label=txid)

            # Directed Edges
            G.add_edge(
                src_ip_node,
                tx_node,
                relationship="observed_source",
                txid=txid,
                src_port=int(row["src_port"]),
                observation_delay_ms=float(row["observation_delay_ms"])
            )
            G.add_edge(
                tx_node,
                dst_ip_node,
                relationship="observed_destination",
                txid=txid,
                dst_port=int(row["dst_port"]),
                observation_delay_ms=float(row["observation_delay_ms"])
            )

    return G
