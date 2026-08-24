# DeSecureFed: Lightweight Encryption and Backdoor-Resilient Aggregation for Decentralized Federated Learning

This repository contains the implementation of DeSecureFed, a decentralized federated learning framework with lightweight hybrid encryption, backdoor-resilient aggregation, and decentralized audit logging.

## Overview

DeSecureFed addresses three critical limitations of existing FL frameworks:
1. **Computational overhead** from homomorphic encryption
2. **Vulnerability** to backdoor attacks
3. **Single-point-of-failure** from centralized aggregation

The framework consists of three core components:
- **LHE (Lightweight Hybrid Encryption)**: AES-256-GCM with Shamir's secret sharing
- **BRA (Backdoor-Resilient Aggregation)**: Spectral anomaly detection on encrypted gradients
- **DAA (Decentralized Aggregation with Audit Log)**: VRF-based committee election with cryptographic audit trails

## Repository Structure

```
desecure-main/
├── desecure.py              # Core DeSecureFed implementation (LHE, BRA, DAA)
├── datasets.py              # Data generation and client creation
├── attacks.py               # Backdoor attack implementations
├── baselines.py            # FL baseline methods (FedProx, FLAME, SCAFFOLD, FedNova)
├── fig.py                  # Figure generation for paper
├── desecurefed_results.csv # Experimental results (10M samples)
└── README.md              # This file
```

## Dependencies

```bash
pip install numpy pandas scikit-learn cryptography matplotlib seaborn
```

## Running Experiments

### Basic Experiment (10M samples)

```bash
python desecure.py
```

This runs the full DeSecureFed experiment with:
- 10 million samples (credit card fraud detection)
- 8 non-IID clients
- 25 training rounds
- Baseline comparisons (FedAvg, FedProx, FLAME, SCAFFOLD, FedNova, SecureFed+)
- Backdoor attack scenario (12.5% attack ratio)

### Custom Sample Size

```bash
python desecure.py --n-samples 5000000
```

## Generating Figures

```bash
python fig.py
```

This generates all figures:
- Accuracy and F1 Score comparison
- Precision and Recall comparison
- Encryption latency scaling
- Backdoor attack resilience
- Training time comparison
- Scalability analysis

Figures are saved as both PDF and PNG formats.

## Experimental Results

Results are saved to `desecurefed_results.csv` with the following metrics:
- Accuracy (%)
- Precision (%)
- Recall (%)
- F1 Score (%)
- AUC
- Detection Rate (%)

### Key Results (10M samples)

| Method | Accuracy (%) | Precision (%) | Recall (%) | F1 (%) |
|--------|-------------|---------------|------------|--------|
| DeSecureFed | 99.96 | 98.29 | 99.71 | 98.99 |
| SecureFed+ | 99.76 | 89.20 | 99.98 | 94.28 |
| FedAvg | 99.48 | 79.46 | 99.96 | 88.54 |
| FedProx | 99.48 | 79.46 | 99.96 | 88.54 |
| FLAME | 99.48 | 79.46 | 99.96 | 88.54 |
| SCAFFOLD | 99.48 | 79.46 | 99.96 | 88.54 |
| FedNova | 99.48 | 79.46 | 99.96 | 88.54 |

## Data Generation

The `datasets.py` module generates synthetic credit card fraud detection data with:
- 30 features (29 PCA components + time + amount)
- 0.5% fraud rate (realistic for credit card fraud)
- SMOTE for class imbalance correction (target 2% fraud rate)
- Non-IID client distribution using Dirichlet (α=0.3)

## Baseline Methods

The following FL baselines are implemented in `baselines.py`:
- **FedAvg**: Standard federated averaging
- **FedProx**: Heterogeneity-aware FL with proximal regularization
- **FLAME**: Clustering-based backdoor defense with Krum
- **SCAFFOLD**: Variance reduction with control variates
- **FedNova**: Objective inconsistency handling via normalization

## Attack Scenarios

The `attacks.py` module implements:
- **SimpleBackdoorAttack**: Sign-flipping attack with trigger pattern
- **AdaptiveBackdoorAttack**: Evasion-based attack (future work)
- **SpectralEvasionAttack**: Clustering-based evasion (future work)

## Core Components

### Lightweight Hybrid Encryption (LHE)
- AES-256-GCM for symmetric encryption
- Shamir's (t,m)-secret sharing for distributed key management
- O(d) complexity (78% faster than Paillier)

### Backdoor-Resilient Aggregation (BRA)
- Spectral anomaly detection on cosine similarity matrices
- Two-stage detection (spectral + contrastive verification)
- Optimal threshold γ = ε/2

### Decentralized Aggregation with Audit Log (DAA)
- VRF-based committee election
- Threshold decryption (t-of-m committee members)
- Cryptographic audit logging with hash chain

## Reproducibility

To reproduce the paper's experimental results:

1. Install dependencies
2. Run the experiment: `python desecure.py`
3. Generate figures: `python fig.py`
4. Results will be saved to `desecurefed_results.csv`
6. Figures will be saved as PDF and PNG files

## Citation

If you use this code, please cite the DeSecureFed paper.

## License

This code is provided for research purposes.
