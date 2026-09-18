import networkx as nx
import pandas as pd


def build_ip_graph(network_obs_df: pd.DataFrame) -> nx.MultiDiGraph:
    """
    Build a directed IP communication MultiDiGraph from Bitcoin P2P network observations.

    Args:
        network_obs_df (pd.DataFrame): Network observations DataFrame.

    Returns:
        nx.MultiDiGraph: NetworkX MultiDiGraph with IP nodes and observation edges.
    """
    G = nx.MultiDiGraph()

    if network_obs_df.empty:
        return G

    for _, row in network_obs_df.iterrows():
        src_ip = str(row["src_ip"]).strip()
        dst_ip = str(row["dst_ip"]).strip()

        # Add IP nodes with node_type attribute
        G.add_node(src_ip, node_type="ip", ip_address=src_ip)
        G.add_node(dst_ip, node_type="ip", ip_address=dst_ip)

        # Edge attributes
        edge_attrs = {
            "txid": str(row["txid"]).strip(),
            "timestamp": str(row["timestamp"]).strip(),
            "src_port": int(row["src_port"]),
            "dst_port": int(row["dst_port"]),
            "observation_delay_ms": float(row["observation_delay_ms"])
        }

        # Add directed edge from src_ip to dst_ip
        G.add_edge(src_ip, dst_ip, **edge_attrs)

    return G
