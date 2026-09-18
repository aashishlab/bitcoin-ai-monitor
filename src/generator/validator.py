import re
import pandas as pd


def validate_dataset(blockchain_tx_df, network_obs_df, entity_wallet_df, ip_mapping_df):
    """
    Validate blockchain transaction and network observation datasets prior to export.

    Args:
        blockchain_tx_df (pd.DataFrame): Blockchain transactions dataset.
        network_obs_df (pd.DataFrame): Network P2P observations dataset.
        entity_wallet_df (pd.DataFrame): Ground truth entity-wallet mapping.
        ip_mapping_df (pd.DataFrame): IP metadata mapping.

    Raises:
        ValueError: If any validation rule is violated.

    Returns:
        bool: True if all checks pass successfully.
    """
    # ----------------------------------------------------
    # 1. Blockchain Transactions Validation
    # ----------------------------------------------------
    required_blockchain_cols = [
        "timestamp", "txid", "input_wallet", "output_wallet",
        "amount", "fee", "script_type", "pattern_label"
    ]
    missing_bc_cols = set(required_blockchain_cols) - set(blockchain_tx_df.columns)
    if missing_bc_cols:
        raise ValueError(f"Validation Error: Missing columns in blockchain transactions: {missing_bc_cols}")

    if blockchain_tx_df[required_blockchain_cols].isnull().any().any():
        raise ValueError("Validation Error: Null values present in blockchain transactions.")

    # TXID Uniqueness
    if blockchain_tx_df["txid"].nunique() != len(blockchain_tx_df):
        raise ValueError("Validation Error: Duplicate TXIDs found in blockchain transactions.")

    # Amount Positivity
    if (blockchain_tx_df["amount"] <= 0).any():
        raise ValueError("Validation Error: Non-positive amounts found in blockchain transactions.")

    # Fee Positivity & Fee < Amount
    if (blockchain_tx_df["fee"] <= 0).any():
        raise ValueError("Validation Error: Non-positive fees found in blockchain transactions.")

    if (blockchain_tx_df["fee"] >= blockchain_tx_df["amount"]).any():
        raise ValueError("Validation Error: Fee >= amount detected in blockchain transactions.")

    # Timestamp format validity
    try:
        pd.to_datetime(blockchain_tx_df["timestamp"])
    except Exception as e:
        raise ValueError(f"Validation Error: Invalid timestamp in blockchain transactions: {e}")

    # Expected pattern labels
    expected_labels = {"normal", "high_value_anomaly", "high_frequency_anomaly", "peeling_chain"}
    found_labels = set(blockchain_tx_df["pattern_label"].unique())
    if expected_labels - found_labels:
        raise ValueError(f"Validation Error: Missing expected pattern labels: {expected_labels - found_labels}")

    # Total Count (~500)
    total_tx_count = len(blockchain_tx_df)
    if not (400 <= total_tx_count <= 650):
        raise ValueError(f"Validation Error: Blockchain transaction count ({total_tx_count}) outside expected range (400-650).")

    # ----------------------------------------------------
    # 2. Network Observations Validation
    # ----------------------------------------------------
    required_net_cols = [
        "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid"
    ]
    missing_net_cols = set(required_net_cols) - set(network_obs_df.columns)
    if missing_net_cols:
        raise ValueError(f"Validation Error: Missing columns in network observations: {missing_net_cols}")

    if network_obs_df[required_net_cols].isnull().any().any():
        raise ValueError("Validation Error: Null values present in network observations.")

    # Valid IPv4 format
    ipv4_regex = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    invalid_src_ips = [ip for ip in network_obs_df["src_ip"].unique() if not ipv4_regex.match(ip)]
    invalid_dst_ips = [ip for ip in network_obs_df["dst_ip"].unique() if not ipv4_regex.match(ip)]
    if invalid_src_ips or invalid_dst_ips:
        raise ValueError(f"Validation Error: Invalid IPv4 format found: src={invalid_src_ips}, dst={invalid_dst_ips}")

    # Valid Port Range (1 - 65535)
    if not ((1 <= network_obs_df["src_port"]) & (network_obs_df["src_port"] <= 65535)).all():
        raise ValueError("Validation Error: Out-of-bounds src_port in network observations.")
    if not ((1 <= network_obs_df["dst_port"]) & (network_obs_df["dst_port"] <= 65535)).all():
        raise ValueError("Validation Error: Out-of-bounds dst_port in network observations.")

    # Foreign Key Check: every observation txid must exist in blockchain_transactions
    bc_txids = set(blockchain_tx_df["txid"])
    net_txids = set(network_obs_df["txid"])
    unmatched_txids = net_txids - bc_txids
    if unmatched_txids:
        raise ValueError(f"Validation Error: Network observations reference non-existent TXIDs: {unmatched_txids}")

    # ----------------------------------------------------
    # 3. Ground Truth Mappings Validation
    # ----------------------------------------------------
    if entity_wallet_df.empty or not set(["wallet_id", "entity_id"]).issubset(entity_wallet_df.columns):
        raise ValueError("Validation Error: Invalid entity_wallet_mapping schema.")

    if ip_mapping_df.empty or not set(["ip_address", "entity_id", "node_type"]).issubset(ip_mapping_df.columns):
        raise ValueError("Validation Error: Invalid ip_mapping schema.")

    print("[VALIDATION SUCCESS] All validation checks passed cleanly!")
    print(f"   - Blockchain Transactions: {total_tx_count}")
    print(f"   - Network Observations: {len(network_obs_df)}")
    print(f"   - Unique Entities: {entity_wallet_df['entity_id'].nunique()}")
    print(f"   - Unique Wallets: {entity_wallet_df['wallet_id'].nunique()}")
    print(f"   - Synthetic IPs: {len(ip_mapping_df)}")
    print(f"   - Pattern Label Distribution:\n{blockchain_tx_df['pattern_label'].value_counts().to_string(header=False)}")
    return True
