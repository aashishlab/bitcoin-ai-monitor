import pandas as pd


def generate_transaction_features(blockchain_df: pd.DataFrame, network_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate transaction-level aggregated features linking blockchain and network metadata.

    Args:
        blockchain_df (pd.DataFrame): Cleaned blockchain transactions.
        network_df (pd.DataFrame): Cleaned network observations.

    Returns:
        pd.DataFrame: Transaction-level features DataFrame (1 row per TXID).
    """
    bc_df = blockchain_df.copy()

    # 1. Compute fee_ratio
    bc_df["fee_ratio"] = (bc_df["fee"] / bc_df["amount"]).round(8)

    # 2. Aggregate network observations per txid
    if not network_df.empty:
        # Helper for unique combined IPs (src + dst) per txid
        def count_unique_total_ips(group):
            src_ips = set(group["src_ip"])
            dst_ips = set(group["dst_ip"])
            return len(src_ips | dst_ips)

        unique_total_ips = network_df.groupby("txid").apply(count_unique_total_ips).reset_index(name="unique_ips")

        net_agg = network_df.groupby("txid").agg(
            network_observation_count=("src_ip", "count"),
            unique_src_ips=("src_ip", "nunique"),
            unique_dst_ips=("dst_ip", "nunique"),
            avg_observation_delay_ms=("observation_delay_ms", lambda x: round(float(x.mean()), 2)),
            min_observation_delay_ms=("observation_delay_ms", "min"),
            max_observation_delay_ms=("observation_delay_ms", "max")
        ).reset_index()

        net_features = pd.merge(net_agg, unique_total_ips, on="txid", how="left")
    else:
        net_features = pd.DataFrame(columns=[
            "txid", "network_observation_count", "unique_src_ips", "unique_dst_ips",
            "unique_ips", "avg_observation_delay_ms", "min_observation_delay_ms", "max_observation_delay_ms"
        ])

    # 3. Merge aggregated network features with blockchain transactions (Left Join)
    features_df = pd.merge(bc_df, net_features, on="txid", how="left")

    # Fill NaNs for transactions with zero network observations
    features_df["network_observation_count"] = features_df["network_observation_count"].fillna(0).astype(int)
    features_df["unique_src_ips"] = features_df["unique_src_ips"].fillna(0).astype(int)
    features_df["unique_dst_ips"] = features_df["unique_dst_ips"].fillna(0).astype(int)
    features_df["unique_ips"] = features_df["unique_ips"].fillna(0).astype(int)
    features_df["avg_observation_delay_ms"] = features_df["avg_observation_delay_ms"].fillna(0.0)
    features_df["min_observation_delay_ms"] = features_df["min_observation_delay_ms"].fillna(0.0)
    features_df["max_observation_delay_ms"] = features_df["max_observation_delay_ms"].fillna(0.0)

    # Reorder columns logically
    ordered_cols = [
        "txid", "timestamp", "input_wallet", "output_wallet", "amount", "fee", "fee_ratio",
        "script_type", "pattern_label", "network_observation_count", "unique_src_ips",
        "unique_dst_ips", "unique_ips", "avg_observation_delay_ms",
        "min_observation_delay_ms", "max_observation_delay_ms"
    ]
    final_cols = [c for c in ordered_cols if c in features_df.columns]
    features_df = features_df[final_cols]

    return features_df
