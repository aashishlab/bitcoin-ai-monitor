import pandas as pd


def correlate_events(blockchain_df: pd.DataFrame, network_df: pd.DataFrame) -> pd.DataFrame:
    """
    Correlate blockchain transactions with network observations on 'txid' (1-to-many).

    Args:
        blockchain_df (pd.DataFrame): Cleaned blockchain transactions.
        network_df (pd.DataFrame): Cleaned network observations.

    Returns:
        pd.DataFrame: Correlated event-level DataFrame.
    """
    # Rename timestamp columns to distinguish transaction time from observation time
    bc_temp = blockchain_df.rename(columns={"timestamp": "timestamp_tx"})
    net_temp = network_df.rename(columns={"timestamp": "timestamp_obs"})

    # Perform inner merge on 'txid'
    correlated_df = pd.merge(
        bc_temp,
        net_temp,
        on="txid",
        how="inner"
    )

    # Reorder columns logically
    column_order = [
        "txid", "input_wallet", "output_wallet", "amount", "fee", "script_type", "pattern_label",
        "timestamp_tx", "timestamp_obs", "src_ip", "dst_ip", "src_port", "dst_port", "observation_delay_ms"
    ]
    # Filter to existing columns in merged dataframe
    final_cols = [c for c in column_order if c in correlated_df.columns]
    correlated_df = correlated_df[final_cols]

    return correlated_df
