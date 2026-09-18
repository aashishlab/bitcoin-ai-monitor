import random
import pandas as pd


def generate_network_metadata(entities, num_ips=50, seed=42):
    """
    Generate synthetic IP addresses mapped to entities and network nodes.

    Args:
        entities (list): List of entity IDs.
        num_ips (int): Total number of synthetic IP addresses (default 50).
        seed (int): Random seed for reproducibility.

    Returns:
        tuple: (ip_mapping_df, ip_to_entity, ip_list)
    """
    random.seed(seed)

    ip_list = []
    # Generate realistic IPv4 addresses
    for _ in range(num_ips):
        first = random.choice([104, 172, 192, 198, 45, 185, 13, 52])
        second = random.randint(1, 254)
        third = random.randint(1, 254)
        fourth = random.randint(1, 254)
        ip = f"{first}.{second}.{third}.{fourth}"
        if ip not in ip_list:
            ip_list.append(ip)

    # Map IPs to entities and network node types
    ip_to_entity = {}
    rows = []

    node_types = ["peer_node", "exchange_node", "mining_pool", "wallet_service", "relay_node"]

    # Assign 1 to 2 IPs to each entity first
    unassigned_ips = ip_list.copy()
    for entity in entities:
        if unassigned_ips:
            ip = unassigned_ips.pop(0)
            node_type = random.choice(node_types)
            ip_to_entity[ip] = entity
            rows.append({
                "ip_address": ip,
                "entity_id": entity,
                "node_type": node_type
            })

    # Assign remaining IPs to random entities or unmapped network nodes
    while unassigned_ips:
        ip = unassigned_ips.pop(0)
        if random.random() < 0.7 and entities:
            entity = random.choice(entities)
            node_type = random.choice(node_types)
            ip_to_entity[ip] = entity
            rows.append({
                "ip_address": ip,
                "entity_id": entity,
                "node_type": node_type
            })
        else:
            ip_to_entity[ip] = "unknown_node"
            rows.append({
                "ip_address": ip,
                "entity_id": "unmapped",
                "node_type": random.choice(["public_peer", "anonymous_proxy"])
            })

    rows.sort(key=lambda x: x["ip_address"])
    ip_mapping_df = pd.DataFrame(rows)

    return ip_mapping_df, ip_to_entity, ip_list


def get_random_ports(seed=None):
    """
    Generate realistic Bitcoin transaction source and destination ports.

    Returns:
        tuple: (src_port, dst_port)
    """
    if seed is not None:
        random.seed(seed)

    # Ephemeral source port range
    src_port = random.randint(49152, 65535)

    # Destination port: 8333 (Bitcoin P2P) ~85% of time, or alternatives
    if random.random() < 0.85:
        dst_port = 8333
    else:
        dst_port = random.choice([8332, 18333, 18332, 80, 443, 8334])

    return src_port, dst_port
