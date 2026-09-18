import re
import pandas as pd


def validate_blockchain_transactions(df: pd.DataFrame) -> bool:
    """
    Validate incoming blockchain transactions dataset independently.

    Args:
        df (pd.DataFrame): Blockchain transactions DataFrame.

    Raises:
        ValueError: If any validation rule fails.

    Returns:
        bool: True if validation passes cleanly.
    """
    required_cols = [
        "timestamp", "txid", "input_wallet", "output_wallet",
        "amount", "fee", "script_type", "pattern_label"
    ]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Validation Error: Blockchain dataset is missing columns: {missing}")

    if df.empty:
        raise ValueError("Validation Error: Blockchain transaction dataset is empty.")

    if df[required_cols].isnull().any().any():
        null_counts = df[required_cols].isnull().sum().to_dict()
        raise ValueError(f"Validation Error: Null values present in blockchain transactions: {null_counts}")

    # Check numeric types for amount and fee
    if not pd.api.types.is_numeric_dtype(df["amount"]):
        try:
            pd.to_numeric(df["amount"])
        except Exception:
            raise ValueError("Validation Error: 'amount' column contains non-numeric values.")

    if not pd.api.types.is_numeric_dtype(df["fee"]):
        try:
            pd.to_numeric(df["fee"])
        except Exception:
            raise ValueError("Validation Error: 'fee' column contains non-numeric values.")

    # Amounts > 0
    if (df["amount"] <= 0).any():
        raise ValueError("Validation Error: Non-positive transaction amounts found.")

    # Fees > 0 and Fee < Amount
    if (df["fee"] <= 0).any():
        raise ValueError("Validation Error: Non-positive transaction fees found.")

    if (df["fee"] >= df["amount"]).any():
        raise ValueError("Validation Error: Transaction fee is greater than or equal to amount.")

    # Unique TXID check
    if df["txid"].nunique() != len(df):
        duplicate_count = len(df) - df["txid"].nunique()
        raise ValueError(f"Validation Error: Found {duplicate_count} duplicate TXID(s) in blockchain transactions.")

    # Parsable timestamp check
    try:
        pd.to_datetime(df["timestamp"])
    except Exception as e:
        raise ValueError(f"Validation Error: Unable to parse timestamps in blockchain transactions: {e}")

    return True


def validate_network_observations(df: pd.DataFrame, blockchain_tx_df: pd.DataFrame = None) -> bool:
    """
    Validate incoming network observations dataset independently.

    Args:
        df (pd.DataFrame): Network observations DataFrame.
        blockchain_tx_df (pd.DataFrame, optional): Blockchain transactions DataFrame for foreign key check.

    Raises:
        ValueError: If any validation rule fails.

    Returns:
        bool: True if validation passes cleanly.
    """
    required_cols = [
        "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid", "observation_delay_ms"
    ]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Validation Error: Network observations dataset is missing columns: {missing}")

    if df.empty:
        raise ValueError("Validation Error: Network observations dataset is empty.")

    if df[required_cols].isnull().any().any():
        null_counts = df[required_cols].isnull().sum().to_dict()
        raise ValueError(f"Validation Error: Null values present in network observations: {null_counts}")

    # Validate IPv4 format
    ipv4_regex = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    invalid_src = [ip for ip in df["src_ip"].unique() if not ipv4_regex.match(str(ip))]
    invalid_dst = [ip for ip in df["dst_ip"].unique() if not ipv4_regex.match(str(ip))]
    if invalid_src or invalid_dst:
        raise ValueError(f"Validation Error: Invalid IPv4 address format found: src={invalid_src}, dst={invalid_dst}")

    # Validate Ports (numeric & between 1 and 65535)
    for port_col in ["src_port", "dst_port"]:
        if not ((1 <= df[port_col]) & (df[port_col] <= 65535)).all():
            raise ValueError(f"Validation Error: Out-of-range port values (1-65535) in '{port_col}'.")

    # Validate observation_delay_ms (numeric & >= 0)
    if (df["observation_delay_ms"] < 0).any():
        raise ValueError("Validation Error: Negative observation_delay_ms values detected.")

    # Parsable timestamp check
    try:
        pd.to_datetime(df["timestamp"])
    except Exception as e:
        raise ValueError(f"Validation Error: Unable to parse timestamps in network observations: {e}")

    # Foreign key check: all observation txids must exist in blockchain_tx_df
    if blockchain_tx_df is not None and not blockchain_tx_df.empty:
        valid_txids = set(blockchain_tx_df["txid"])
        obs_txids = set(df["txid"])
        unmatched = obs_txids - valid_txids
        if unmatched:
            raise ValueError(f"Validation Error: {len(unmatched)} TXIDs in network observations do not exist in blockchain transactions dataset.")

    return True
