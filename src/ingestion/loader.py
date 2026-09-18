import os
import sys
import pandas as pd


def load_csv_file(file_path: str, required_columns: list) -> pd.DataFrame:
    """
    Safely load a CSV file with error handling.

    Args:
        file_path (str): Path to the CSV file.
        required_columns (list): Mandatory columns expected in the dataset.

    Returns:
        pd.DataFrame: Loaded DataFrame.

    Raises:
        ValueError: If file is missing, empty, invalid, or missing required columns.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Ingestion Error: File not found at '{file_path}'")

    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"Ingestion Error: File at '{file_path}' is completely empty.")
    except Exception as e:
        raise ValueError(f"Ingestion Error: Failed to parse CSV at '{file_path}': {e}")

    if df.empty:
        raise ValueError(f"Ingestion Error: Dataset at '{file_path}' contains zero rows.")

    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Ingestion Error: File '{os.path.basename(file_path)}' is missing required columns: {missing}")

    return df


def load_raw_data(data_dir: str = "data/raw") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all four raw CSV datasets from the target directory.

    Args:
        data_dir (str): Path to the directory containing raw CSV files.

    Returns:
        tuple: (blockchain_tx_df, network_obs_df, entity_wallet_df, ip_mapping_df)
    """
    if not os.path.isabs(data_dir):
        # Resolve path relative to repository root if relative
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../"))
        data_dir = os.path.join(project_root, data_dir)

    bc_cols = ["timestamp", "txid", "input_wallet", "output_wallet", "amount", "fee", "script_type", "pattern_label"]
    net_cols = ["timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid", "observation_delay_ms"]
    ew_cols = ["wallet_id", "entity_id"]
    ip_cols = ["ip_address", "entity_id", "node_type"]

    bc_tx_df = load_csv_file(os.path.join(data_dir, "blockchain_transactions.csv"), bc_cols)
    net_obs_df = load_csv_file(os.path.join(data_dir, "network_observations.csv"), net_cols)
    ew_df = load_csv_file(os.path.join(data_dir, "entity_wallet_mapping.csv"), ew_cols)
    ip_df = load_csv_file(os.path.join(data_dir, "ip_mapping.csv"), ip_cols)

    return bc_tx_df, net_obs_df, ew_df, ip_df
