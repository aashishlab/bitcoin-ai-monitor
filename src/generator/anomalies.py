from datetime import timedelta
import random
import numpy as np


def generate_anomalies(wallets, start_tx_id, base_timestamp, num_high_value=18, num_high_freq=18, seed=42):
    """
    Generate high-value and high-frequency anomaly blockchain transactions.

    Args:
        wallets (list): Available wallet IDs.
        start_tx_id (int): Starting TXID numeric index.
        base_timestamp (datetime): Reference timestamp to inject anomalies around.
        num_high_value (int): Number of high-value anomalies.
        num_high_freq (int): Number of high-frequency anomalies.
        seed (int): Random seed for reproducibility.

    Returns:
        tuple: (anomaly_transactions_list, next_tx_id)
    """
    random.seed(seed)
    np.random.seed(seed)

    transactions = []
    current_tx_id = start_tx_id
    script_types = ["P2PKH", "P2SH", "P2WPKH"]

    # 1. High-Value Anomalies
    for i in range(num_high_value):
        time_offset = timedelta(minutes=random.randint(10, 4000))
        tx_time = base_timestamp + time_offset

        input_wallet, output_wallet = random.sample(wallets, 2)
        amount = round(random.uniform(100.0, 1200.0), 8)
        fee = round(random.uniform(0.001, 0.05), 8)

        tx_record = {
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "txid": f"TX_{current_tx_id:06d}",
            "input_wallet": input_wallet,
            "output_wallet": output_wallet,
            "amount": amount,
            "fee": fee,
            "script_type": random.choice(script_types),
            "pattern_label": "high_value_anomaly"
        }
        transactions.append(tx_record)
        current_tx_id += 1

    # 2. High-Frequency Anomalies (rapid burst from selected target wallet)
    target_wallet = random.choice(wallets)
    burst_start_time = base_timestamp + timedelta(hours=12)

    for i in range(num_high_freq):
        burst_start_time += timedelta(seconds=random.randint(2, 20))
        output_wallet = random.choice([w for w in wallets if w != target_wallet])

        amount = round(random.uniform(0.01, 0.5), 8)
        fee = round(0.0001, 8)

        tx_record = {
            "timestamp": burst_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "txid": f"TX_{current_tx_id:06d}",
            "input_wallet": target_wallet,
            "output_wallet": output_wallet,
            "amount": amount,
            "fee": fee,
            "script_type": random.choice(script_types),
            "pattern_label": "high_frequency_anomaly"
        }
        transactions.append(tx_record)
        current_tx_id += 1

    return transactions, current_tx_id
