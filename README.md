# AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

## 📌 Overview

An offline-capable system for analyzing Bitcoin blockchain and P2P network metadata using **data processing, graph analytics, and AI/ML**.

The system correlates transactions, wallets, TXIDs, IP/port observations, and entities to detect suspicious activity and generate investigative insights.

---

## 📂 Project Structure

```text
bitcoin-ai-monitor/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── .gitkeep
│   │   ├── blockchain_transactions.csv
│   │   ├── entity_wallet_mapping.csv
│   │   ├── ip_mapping.csv
│   │   └── network_observations.csv
│   └── processed/
│       ├── .gitkeep
│       ├── correlated_events.csv
│       ├── graph_summary.json
│       ├── investigation_graph.graphml
│       ├── ip_graph.graphml
│       ├── ip_graph_metrics.csv
│       ├── transaction_features.csv
│       ├── wallet_graph.graphml
│       └── wallet_graph_metrics.csv
├── docs/
│   └── phase4_graph.md
├── geoip/
│   └── .gitkeep
├── lib/
│   ├── bindings/
│   ├── tom-select/
│   └── vis-9.1.2/
├── models/
│   └── .gitkeep
├── output/
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── graph_visualizer.py
│   │   └── ui_components.py
│   ├── detection/
│   │   └── __init__.py
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── anomalies.py
│   │   ├── entities.py
│   │   ├── generate_dataset.py
│   │   ├── network.py
│   │   ├── network_observations.py
│   │   ├── normal_transactions.py
│   │   ├── peeling_chain.py
│   │   └── validator.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── exporter.py
│   │   ├── investigation_graph.py
│   │   ├── ip_graph.py
│   │   ├── metrics.py
│   │   ├── run_graph_pipeline.py
│   │   └── wallet_graph.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── loader.py
│   ├── ml/
│   │   └── __init__.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   ├── correlator.py
│   │   ├── features.py
│   │   ├── run_pipeline.py
│   │   └── validator.py
│   └── scoring/
│       └── __init__.py
└── tests/
    └── .gitkeep
```

---

## 🚀 Current Progress

- ✅ **Phase 1:** Project Setup
- ✅ **Phase 2:** Synthetic Data Generation
  - 510 transactions
  - 1,497 network observations
  - 100 wallets, 20 entities, 50 IPs
  - Normal, high-value, high-frequency, and peeling-chain patterns
- ✅ **Phase 3:** Data Processing
  - Validation, cleaning, TXID correlation, and feature engineering
- ✅ **Phase 4:** Graph Analysis & Dashboard
  - Wallet, IP, and investigation graphs
  - Graph metrics and interactive visualization
- ⏳ **Next:** Phase 5 — AI/ML Anomaly Detection

---

## ⚙️ Installation

```bash
python -m venv venv
```

### Windows

```powershell
.\venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Project

### Generate Data

```bash
python src/generator/generate_dataset.py
```

### Run Processing Pipeline

```bash
python src/preprocessing/run_pipeline.py
```

### Build Investigation Graph

```bash
python src/graph/run_graph_pipeline.py
```

### Launch Dashboard

```bash
streamlit run src/dashboard/app.py
```

---

## 🐧 Offline & Linux Support

Designed to run locally and offline after dependencies and datasets are installed.

```text
Data → Processing → Correlation → Features
     → Graph Analysis → AI/ML → Risk Scoring → Dashboard
```

---

## 🔮 Upcoming Features

- AI/ML anomaly detection
- Suspicious pattern detection
- Entity clustering
- Risk scoring and explainable alerts
- GeoIP/ASN integration
- Final investigation dashboard