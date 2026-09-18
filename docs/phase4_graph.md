# Phase 4 — Entity–Wallet–Transaction–IP Investigation Graph & Prototype UI

## Overview
Phase 4 builds a heterogeneous investigation graph from Bitcoin blockchain transaction logs and P2P network layer observations. It establishes structural graph models, computes graph centrality metrics, exports standardized GraphML and metrics files, and provides an offline interactive Streamlit UI for visual graph exploration.

---

## Conceptual Architecture

```text
Synthetic Entity Node (entity:entity_001)
      │
      │ owns
      ▼
Input Wallet Node (wallet:wallet_001)
      │
      │ input_to
      ▼
Transaction Node (tx:TX_000001)
      │                     ▲
      │ output_to           │ observed_source / observed_destination
      ▼                     │
Output Wallet Node (wallet:wallet_050) ── IP Node (ip:104.144.51.184)
```

---

## Datasets Consumed
- `data/raw/blockchain_transactions.csv`
- `data/raw/network_observations.csv`
- `data/raw/entity_wallet_mapping.csv`
- `data/raw/ip_mapping.csv`
- `data/processed/correlated_events.csv`
- `data/processed/transaction_features.csv`

---

## Graph Construction Models

### 1. Wallet Transaction Graph (`wallet_graph.py`)
- **Type:** `networkx.MultiDiGraph`
- **Edges:** `input_wallet` → `output_wallet`
- **Attributes:** `txid`, `amount`, `fee`, `timestamp`, `script_type`, `pattern_label`.

### 2. IP Communication Graph (`ip_graph.py`)
- **Type:** `networkx.MultiDiGraph`
- **Edges:** `src_ip` → `dst_ip`
- **Attributes:** `txid`, `timestamp`, `src_port`, `dst_port`, `observation_delay_ms`.

### 3. Combined Investigation Graph (`investigation_graph.py`)
- **Type:** Heterogeneous `networkx.MultiDiGraph`
- **Prefixed Node IDs:**
  - `wallet:<wallet_id>` (`node_type="wallet"`)
  - `tx:<txid>` (`node_type="transaction"`)
  - `ip:<ip_address>` (`node_type="ip"`)
  - `entity:<entity_id>` (`node_type="entity"`)
- **Edge Relationships:**
  - `owns`: Entity → Wallet
  - `input_to`: Input Wallet → Transaction
  - `output_to`: Transaction → Output Wallet
  - `observed_source`: Source IP → Transaction
  - `observed_destination`: Transaction → Destination IP

---

## Graph Metrics (`metrics.py`)
- `in_degree`, `out_degree`, `total_degree`
- `degree_centrality`
- `pagerank`
- `betweenness_centrality`
- Aggregated summary statistics (node counts by type, total edges, weakly connected components).

---

## Generated Export Files in `data/processed/`
- `wallet_graph_metrics.csv`
- `ip_graph_metrics.csv`
- `investigation_graph.graphml`
- `wallet_graph.graphml`
- `ip_graph.graphml`
- `graph_summary.json`

---

## Running the Pipeline

### 1. Execute Graph Pipeline
```bash
python src/graph/run_graph_pipeline.py
```

### 2. Launch Interactive Streamlit Prototype UI
```bash
streamlit run src/dashboard/app.py
```
