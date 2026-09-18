import networkx as nx
import pandas as pd


def build_wallet_graph(transactions_df: pd.DataFrame) -> nx.MultiDiGraph:
    """
    Build a directed wallet transaction MultiDiGraph representing BTC transfer flow.

    Args:
        transactions_df (pd.DataFrame): Blockchain transactions DataFrame.

    Returns:
        nx.MultiDiGraph: NetworkX MultiDiGraph with wallet nodes and transaction edges.
    """
    G = nx.MultiDiGraph()

    if transactions_df.empty:
        return G

    for _, row in transactions_df.iterrows():
        src_wallet = str(row["input_wallet"]).strip()
        dst_wallet = str(row["output_wallet"]).strip()

        # Add wallet nodes with node_type attribute
        G.add_node(src_wallet, node_type="wallet", wallet_id=src_wallet)
        G.add_node(dst_wallet, node_type="wallet", wallet_id=dst_wallet)

        # Edge attributes
        edge_attrs = {
            "txid": str(row["txid"]).strip(),
            "amount": float(row["amount"]),
            "fee": float(row["fee"]),
            "timestamp": str(row["timestamp"]).strip(),
            "script_type": str(row["script_type"]).strip(),
            "pattern_label": str(row["pattern_label"]).strip()
        }

        # Add directed edge from input_wallet to output_wallet
        G.add_edge(src_wallet, dst_wallet, **edge_attrs)

    return G
