import os
import sys
import pandas as pd

# Ensure repository root is in python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.ingestion.loader import load_raw_data
from src.preprocessing.cleaner import clean_blockchain_transactions, clean_network_observations
from src.preprocessing.correlator import correlate_events
from src.preprocessing.features import generate_transaction_features
from src.preprocessing.validator import validate_blockchain_transactions, validate_network_observations


def run_pipeline(raw_dir: str = "data/raw", processed_dir: str = "data/processed") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute complete Phase 3 Data Processing Pipeline.

    Args:
        raw_dir (str): Relative or absolute path to raw data folder.
        processed_dir (str): Relative or absolute path to processed output folder.

    Returns:
        tuple: (correlated_events_df, transaction_features_df)
    """
    print("[INFO] Starting Phase 3 Data Processing Pipeline...\n")

    # Step 1: Loading
    print("[1/6] Loading raw datasets...")
    raw_path = os.path.isabs(raw_dir) and raw_dir or os.path.join(project_root, raw_dir)
    bc_raw, net_raw, ew_raw, ip_raw = load_raw_data(data_dir=raw_path)
    print(f"      Blockchain Transactions: {len(bc_raw)}")
    print(f"      Network Observations: {len(net_raw)}")

    # Step 2: Validation
    print("\n[2/6] Validating datasets...")
    validate_blockchain_transactions(bc_raw)
    validate_network_observations(net_raw, blockchain_tx_df=bc_raw)
    print("      Validation successful.")

    # Step 3: Cleaning & Normalization
    print("\n[3/6] Cleaning and normalizing data...")
    bc_clean = clean_blockchain_transactions(bc_raw)
    net_clean = clean_network_observations(net_raw)
    print("      Cleaning completed.")

    # Step 4: Correlation (Event-Level)
    print("\n[4/6] Correlating transactions with network observations...")
    correlated_events_df = correlate_events(bc_clean, net_clean)
    print(f"      Correlation completed ({len(correlated_events_df)} event records).")

    # Step 5: Feature Aggregation (Transaction-Level)
    print("\n[5/6] Generating transaction-level features...")
    tx_features_df = generate_transaction_features(bc_clean, net_clean)
    print("      Features generated successfully.")

    # Step 6: Export Processed Datasets
    print("\n[6/6] Saving processed datasets...")
    out_path = os.path.isabs(processed_dir) and processed_dir or os.path.join(project_root, processed_dir)
    os.makedirs(out_path, exist_ok=True)

    corr_file = os.path.join(out_path, "correlated_events.csv")
    feat_file = os.path.join(out_path, "transaction_features.csv")

    correlated_events_df.to_csv(corr_file, index=False)
    tx_features_df.to_csv(feat_file, index=False)

    # Compute Summary Statistics
    txs_with_obs = (tx_features_df["network_observation_count"] > 0).sum()
    unique_wallets = len(set(bc_clean["input_wallet"]) | set(bc_clean["output_wallet"]))
    unique_ips = len(set(net_clean["src_ip"]) | set(net_clean["dst_ip"]))

    print("\n[SUCCESS] Phase 3 completed successfully.\n")
    print("Summary:")
    print(f"- Total Blockchain Transactions: {len(bc_clean)}")
    print(f"- Total Network Observations: {len(net_clean)}")
    print(f"- Correlated Events: {len(correlated_events_df)}")
    print(f"- Transactions With Network Observations: {txs_with_obs}")
    print(f"- Unique Wallets: {unique_wallets}")
    print(f"- Unique IPs: {unique_ips}")

    print("\nGenerated files:")
    print(f"data/processed/correlated_events.csv ({len(correlated_events_df)} rows)")
    print(f"data/processed/transaction_features.csv ({len(tx_features_df)} rows)")

    return correlated_events_df, tx_features_df


if __name__ == "__main__":
    run_pipeline()
