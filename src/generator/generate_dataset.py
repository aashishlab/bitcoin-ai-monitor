from datetime import datetime
import os
import sys
import pandas as pd

# Ensure repository root is in python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.generator.anomalies import generate_anomalies
from src.generator.entities import generate_entities_and_wallets
from src.generator.network import generate_network_metadata
from src.generator.network_observations import generate_network_observations
from src.generator.normal_transactions import generate_normal_transactions
from src.generator.peeling_chain import generate_peeling_chains
from src.generator.validator import validate_dataset


def generate_full_dataset(output_dir="data/raw", seed=42):
    """
    Main generator pipeline for synthetic Bitcoin transaction and network dataset.

    Args:
        output_dir (str): Relative or absolute path to data/raw output directory.
        seed (int): Fixed random seed for complete reproducibility.
    """
    print("[INFO] Synthetic Bitcoin Dataset Generator\n")

    # Step 1: Generate Entities and Wallets
    entity_wallet_df, entities, wallets, _ = generate_entities_and_wallets(
        num_entities=20, total_wallets=100, seed=seed
    )
    print(f"[1/7] Generated entities and wallets ({len(entities)} entities, {len(wallets)} wallets).")

    # Step 2: Generate Network IP Metadata
    ip_mapping_df, ip_to_entity, ip_list = generate_network_metadata(
        entities=entities, num_ips=50, seed=seed
    )
    print(f"[2/7] Generated network IP mappings ({len(ip_list)} IPs).")

    # Step 3: Generate Normal Blockchain Transactions (~450)
    base_start_time = datetime(2026, 3, 1, 0, 0, 0)
    normal_txs, next_tx_id, last_time = generate_normal_transactions(
        wallets=wallets,
        start_tx_id=1,
        num_txs=450,
        start_time=base_start_time,
        seed=seed
    )
    print(f"[3/7] Generated normal blockchain transactions ({len(normal_txs)} txs).")

    # Step 4: Inject Anomaly Transactions (~36)
    anomaly_txs, next_tx_id = generate_anomalies(
        wallets=wallets,
        start_tx_id=next_tx_id,
        base_timestamp=base_start_time,
        num_high_value=18,
        num_high_freq=18,
        seed=seed
    )
    print(f"[4/7] Injected anomaly transactions ({len(anomaly_txs)} high-value & high-frequency).")

    # Step 5: Generate Peeling-Chain Transactions (~24)
    peeling_txs, next_tx_id = generate_peeling_chains(
        wallets=wallets,
        start_tx_id=next_tx_id,
        base_timestamp=base_start_time,
        num_chains=3,
        chain_length=4,
        seed=seed
    )
    print(f"[5/7] Generated peeling-chain transactions ({len(peeling_txs)} txs across 3 chains).")

    # Combine all blockchain transaction batches
    all_blockchain_txs = normal_txs + anomaly_txs + peeling_txs
    blockchain_tx_df = pd.DataFrame(all_blockchain_txs)

    # Sort blockchain transactions chronologically by timestamp
    blockchain_tx_df["timestamp"] = pd.to_datetime(blockchain_tx_df["timestamp"])
    blockchain_tx_df = blockchain_tx_df.sort_values(by="timestamp").reset_index(drop=True)
    blockchain_tx_df["timestamp"] = blockchain_tx_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Step 6: Generate Correlated Network Observations
    network_obs_records = generate_network_observations(
        transactions=all_blockchain_txs,
        ip_list=ip_list,
        seed=seed
    )
    network_obs_df = pd.DataFrame(network_obs_records)
    print(f"[6/7] Generated correlated network observations ({len(network_obs_df)} observations).")

    # Step 7: Validate Datasets
    print("\n[7/7] Validating datasets...")
    validate_dataset(blockchain_tx_df, network_obs_df, entity_wallet_df, ip_mapping_df)

    # Export to CSV
    target_dir = os.path.isabs(output_dir) and output_dir or os.path.join(project_root, output_dir)
    os.makedirs(target_dir, exist_ok=True)

    bc_tx_path = os.path.join(target_dir, "blockchain_transactions.csv")
    net_obs_path = os.path.join(target_dir, "network_observations.csv")
    ew_path = os.path.join(target_dir, "entity_wallet_mapping.csv")
    ip_path = os.path.join(target_dir, "ip_mapping.csv")

    blockchain_tx_df.to_csv(bc_tx_path, index=False)
    network_obs_df.to_csv(net_obs_path, index=False)
    entity_wallet_df.to_csv(ew_path, index=False)
    ip_mapping_df.to_csv(ip_path, index=False)

    # Clean up deprecated single transactions.csv file if present
    deprecated_tx_path = os.path.join(target_dir, "transactions.csv")
    if os.path.exists(deprecated_tx_path):
        os.remove(deprecated_tx_path)

    print("\n[SUCCESS] Files generated:")
    print(f"data/raw/blockchain_transactions.csv ({len(blockchain_tx_df)} rows)")
    print(f"data/raw/network_observations.csv ({len(network_obs_df)} rows)")
    print(f"data/raw/entity_wallet_mapping.csv ({len(entity_wallet_df)} rows)")
    print(f"data/raw/ip_mapping.csv ({len(ip_mapping_df)} rows)")


if __name__ == "__main__":
    generate_full_dataset()
