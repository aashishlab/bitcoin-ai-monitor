from datetime import datetime, timedelta
import random
import numpy as np


def generate_normal_transactions(wallets, start_tx_id=1, num_txs=450, start_time=None, seed=42):
    """
    Generate normal Bitcoin blockchain transaction records.

    Args:
        wallets (list): List of available wallet IDs.
        start_tx_id (int): Starting transaction numeric ID.
        num_txs (int): Number of normal transactions to generate.
        start_time (datetime): Base start timestamp for transactions.
        seed (int): Random seed for reproducibility.

    Returns:
        tuple: (transactions_list, next_tx_id, last_timestamp)
    """
    random.seed(seed)
    np.random.seed(seed)

    if start_time is None:
        start_time = datetime(2026, 3, 1, 0, 0, 0)

    current_time = start_time
    transactions = []
    current_tx_id = start_tx_id

    script_types = ["P2PKH", "P2SH", "P2WPKH"]
    script_weights = [0.50, 0.30, 0.20]

    for _ in range(num_txs):
        # Timestamps with realistic variation (1 to 45 minutes between normal txs)
        delta_seconds = int(np.random.exponential(scale=1200) + 10)
        current_time += timedelta(seconds=delta_seconds)

        # Pick distinct input and output wallets
        input_wallet, output_wallet = random.sample(wallets, 2)

        # Skewed amount distribution using Log-Normal (mean small, rare large)
        raw_amount = np.random.lognormal(mean=-1.5, sigma=1.2)
        amount = round(max(0.001, min(raw_amount, 25.0)), 8)

        # Fee: ~0.01% to 0.5% of amount + base fee 0.00005, strictly < amount
        raw_fee = (amount * random.uniform(0.0001, 0.005)) + 0.00005
        fee = round(min(raw_fee, amount * 0.1, 0.005), 8)

        script_type = random.choices(script_types, weights=script_weights)[0]

        tx_record = {
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "txid": f"TX_{current_tx_id:06d}",
            "input_wallet": input_wallet,
            "output_wallet": output_wallet,
            "amount": amount,
            "fee": fee,
            "script_type": script_type,
            "pattern_label": "normal"
        }

        transactions.append(tx_record)
        current_tx_id += 1

    return transactions, current_tx_id, current_time
