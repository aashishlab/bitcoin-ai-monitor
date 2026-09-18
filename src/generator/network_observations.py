from datetime import datetime, timedelta
import random
from src.generator.network import get_random_ports


def generate_network_observations(transactions, ip_list, seed=42):
    """
    Generate correlated network P2P observations for blockchain transactions.

    Args:
        transactions (list of dict): List of blockchain transaction records.
        ip_list (list): Available synthetic IP addresses.
        seed (int): Random seed for reproducibility.

    Returns:
        list of dict: Network observation records linked by txid.
    """
    random.seed(seed)

    observations = []

    for tx in transactions:
        tx_id = tx["txid"]
        tx_timestamp = datetime.strptime(tx["timestamp"], "%Y-%m-%d %H:%M:%S")

        # Generate 1 to 5 network observations per transaction to simulate node propagation
        num_observations = random.randint(1, 5)

        accumulated_delay = 0

        for hop in range(num_observations):
            # Propagation delay in milliseconds (50ms to 800ms per hop)
            hop_delay = random.randint(50, 800)
            accumulated_delay += hop_delay

            obs_timestamp = tx_timestamp + timedelta(milliseconds=accumulated_delay)

            src_ip = random.choice(ip_list)
            dst_ip = random.choice([ip for ip in ip_list if ip != src_ip] or ip_list)

            src_port, dst_port = get_random_ports()

            obs_record = {
                "timestamp": obs_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "txid": tx_id,
                "observation_delay_ms": accumulated_delay
            }

            observations.append(obs_record)

    # Sort observations by timestamp
    observations.sort(key=lambda x: x["timestamp"])
    return observations
