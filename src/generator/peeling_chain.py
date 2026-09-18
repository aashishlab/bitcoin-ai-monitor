from datetime import timedelta
import random


def generate_peeling_chains(wallets, start_tx_id, base_timestamp, num_chains=3, chain_length=4, seed=42):
    """
    Generate synthetic peeling chain blockchain transactions.

    In a peeling chain:
    - Wallet_A sends large remaining balance to Wallet_B, peeling a smaller amount to Side_Wallet_1.
    - Wallet_B sends remaining balance to Wallet_C, peeling a smaller amount to Side_Wallet_2.

    Args:
        wallets (list): Available wallet IDs.
        start_tx_id (int): Starting TXID numeric index.
        base_timestamp (datetime): Base timestamp for starting the chains.
        num_chains (int): Number of distinct peeling chains (default 3).
        chain_length (int): Number of hops per peeling chain.
        seed (int): Random seed for reproducibility.

    Returns:
        tuple: (peeling_transactions_list, next_tx_id)
    """
    random.seed(seed)

    transactions = []
    current_tx_id = start_tx_id
    script_types = ["P2PKH", "P2SH", "P2WPKH"]

    for chain_idx in range(num_chains):
        chain_wallets = random.sample(wallets, chain_length + 1)
        side_wallets = random.sample([w for w in wallets if w not in chain_wallets], chain_length)

        current_chain_time = base_timestamp + timedelta(hours=random.randint(5, 48))
        initial_balance = round(random.uniform(50.0, 150.0), 8)
        current_balance = initial_balance

        for hop in range(chain_length):
            input_w = chain_wallets[hop]
            next_chain_w = chain_wallets[hop + 1]
            side_w = side_wallets[hop]

            peeled_amount = round(current_balance * random.uniform(0.01, 0.05), 8)
            fee1 = 0.0001
            main_tx_amount = round(current_balance - peeled_amount - (fee1 * 2), 8)

            if main_tx_amount <= 0 or peeled_amount <= 0:
                break

            current_chain_time += timedelta(minutes=random.randint(2, 15))

            # 1. Main chain continuation transaction
            tx_main = {
                "timestamp": current_chain_time.strftime("%Y-%m-%d %H:%M:%S"),
                "txid": f"TX_{current_tx_id:06d}",
                "input_wallet": input_w,
                "output_wallet": next_chain_w,
                "amount": main_tx_amount,
                "fee": fee1,
                "script_type": random.choice(script_types),
                "pattern_label": "peeling_chain"
            }
            transactions.append(tx_main)
            current_tx_id += 1

            # 2. Peeled side transaction
            tx_side = {
                "timestamp": (current_chain_time + timedelta(seconds=random.randint(1, 5))).strftime("%Y-%m-%d %H:%M:%S"),
                "txid": f"TX_{current_tx_id:06d}",
                "input_wallet": input_w,
                "output_wallet": side_w,
                "amount": peeled_amount,
                "fee": fee1,
                "script_type": random.choice(script_types),
                "pattern_label": "peeling_chain"
            }
            transactions.append(tx_side)
            current_tx_id += 1

            current_balance = main_tx_amount

    return transactions, current_tx_id
