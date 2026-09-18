import pandas as pd


def clean_blockchain_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize blockchain transaction records.

    Args:
        df (pd.DataFrame): Raw blockchain transactions DataFrame.

    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame.
    """
    cleaned_df = df.copy()
    initial_count = len(cleaned_df)

    # 1. Strip whitespace from column names
    cleaned_df.columns = [col.strip() for col in cleaned_df.columns]

    # 2. Remove exact duplicate rows
    cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
    duplicates_removed = initial_count - len(cleaned_df)

    # 3. Convert data types
    cleaned_df["timestamp"] = pd.to_datetime(cleaned_df["timestamp"])
    cleaned_df["amount"] = pd.to_numeric(cleaned_df["amount"], errors="coerce").astype(float)
    cleaned_df["fee"] = pd.to_numeric(cleaned_df["fee"], errors="coerce").astype(float)
    cleaned_df["txid"] = cleaned_df["txid"].astype(str).str.strip()
    cleaned_df["input_wallet"] = cleaned_df["input_wallet"].astype(str).str.strip()
    cleaned_df["output_wallet"] = cleaned_df["output_wallet"].astype(str).str.strip()
    cleaned_df["script_type"] = cleaned_df["script_type"].astype(str).str.strip()
    cleaned_df["pattern_label"] = cleaned_df["pattern_label"].astype(str).str.strip()

    # 4. Sort chronologically
    cleaned_df = cleaned_df.sort_values(by="timestamp").reset_index(drop=True)

    print(f"      [Cleaner] Blockchain Transactions: {initial_count} initial, {duplicates_removed} duplicates removed, {len(cleaned_df)} final.")
    return cleaned_df


def clean_network_observations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize network observation records.

    Args:
        df (pd.DataFrame): Raw network observations DataFrame.

    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame.
    """
    cleaned_df = df.copy()
    initial_count = len(cleaned_df)

    # 1. Strip whitespace from column names
    cleaned_df.columns = [col.strip() for col in cleaned_df.columns]

    # 2. Remove exact duplicate rows
    cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
    duplicates_removed = initial_count - len(cleaned_df)

    # 3. Convert data types
    cleaned_df["timestamp"] = pd.to_datetime(cleaned_df["timestamp"])
    cleaned_df["src_ip"] = cleaned_df["src_ip"].astype(str).str.strip()
    cleaned_df["dst_ip"] = cleaned_df["dst_ip"].astype(str).str.strip()
    cleaned_df["src_port"] = pd.to_numeric(cleaned_df["src_port"], errors="coerce").astype(int)
    cleaned_df["dst_port"] = pd.to_numeric(cleaned_df["dst_port"], errors="coerce").astype(int)
    cleaned_df["txid"] = cleaned_df["txid"].astype(str).str.strip()
    cleaned_df["observation_delay_ms"] = pd.to_numeric(cleaned_df["observation_delay_ms"], errors="coerce").astype(float)

    # 4. Sort chronologically
    cleaned_df = cleaned_df.sort_values(by="timestamp").reset_index(drop=True)

    print(f"      [Cleaner] Network Observations: {initial_count} initial, {duplicates_removed} duplicates removed, {len(cleaned_df)} final.")
    return cleaned_df
