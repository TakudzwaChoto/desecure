"""
DeSecureFed: Multiple Dataset Support
Healthcare EHR, IoT Anomaly Detection, and Recommender Systems
Supports up to 3 billion samples with memory-efficient batch processing
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import os


def generate_data(n_samples=30000, fraud_rate=0.005, target_fraud_rate=0.02, batch_size=1000000):
    """
    Generate data in batches to support up to 3 billion samples
    Uses memory-mapped files for large-scale datasets to avoid RAM limitations
    Returns memmap arrays for large datasets to keep data on disk
    """
    np.random.seed(42)
    n_features = 20
    n_fraud = int(n_samples * fraud_rate)
    n_normal = n_samples - n_fraud
    
    # For large datasets, use memory-mapped files and keep them on disk
    if n_samples > 1000000:
        print(f"Generating {n_samples:,} samples using memory-mapped files...")
        
        # Create temporary memmap files
        X_file = 'temp_X.dat'
        y_file = 'temp_y.dat'
        
        # Calculate final size after SMOTE
        n_minority = n_fraud
        n_majority = n_normal
        target_minority = int(n_majority * target_fraud_rate / (1 - target_fraud_rate))
        final_size = n_majority + target_minority
        
        # Create memmap arrays
        X_memmap = np.memmap(X_file, dtype='float64', mode='w+', shape=(final_size, n_features))
        y_memmap = np.memmap(y_file, dtype='float64', mode='w+', shape=(final_size,))
        
        # Generate normal samples
        print(f"Generating {n_normal:,} normal samples...")
        for i in range(0, n_normal, batch_size):
            end = min(i + batch_size, n_normal)
            batch_size_actual = end - i
            X_memmap[i:end] = np.random.randn(batch_size_actual, n_features) * 0.8
            y_memmap[i:end] = 0
            if i % (batch_size * 10) == 0:
                print(f"  Generated {end:,} / {n_normal:,} normal samples...")
        
        # Generate fraud samples
        print(f"Generating {n_fraud:,} fraud samples...")
        for i in range(n_normal, n_normal + n_fraud, batch_size):
            end = min(i + batch_size, n_normal + n_fraud)
            batch_size_actual = end - i
            X_fraud_batch = np.random.randn(batch_size_actual, n_features) * 0.8
            X_fraud_batch[:, 0] += 3.0
            X_fraud_batch[:, 1] += 2.5
            X_fraud_batch[:, 2] -= 2.0
            X_fraud_batch[:, 3] += 2.0
            X_fraud_batch[:, 4] += 1.5
            X_memmap[i:end] = X_fraud_batch
            y_memmap[i:end] = 1
            if i % (batch_size * 10) == 0:
                print(f"  Generated {end - n_normal:,} / {n_fraud:,} fraud samples...")
        
        # Shuffle in chunks for memmap to avoid memory issues
        print("Shuffling data in chunks...")
        n_total = n_normal + n_fraud
        chunk_size = 1000000  # 1M chunks
        
        # Generate permutation indices in chunks
        for i in range(0, n_total, chunk_size):
            end = min(i + chunk_size, n_total)
            chunk_indices = np.arange(i, end)
            np.random.shuffle(chunk_indices)
            
            # Swap rows within chunk
            for k, new_pos in enumerate(chunk_indices):
                if new_pos != i + k:
                    X_memmap[[i + k, new_pos]] = X_memmap[[new_pos, i + k]]
                    y_memmap[[i + k, new_pos]] = y_memmap[[new_pos, i + k]]
            
            if i % (chunk_size * 10) == 0:
                print(f"  Shuffled {end:,} / {n_total:,} samples...")
        
        # Apply SMOTE
        current_fraud_rate = np.mean(y_memmap[:n_normal + n_fraud])
        if current_fraud_rate < target_fraud_rate:
            print(f"Applying SMOTE to increase fraud rate from {current_fraud_rate*100:.2f}% to {target_fraud_rate*100:.2f}%...")
            
            minority_indices = np.where(y_memmap[:n_normal + n_fraud] == 1)[0]
            n_to_add = target_minority - n_minority
            
            if n_to_add > 0:
                for i in range(n_normal + n_fraud, final_size, batch_size):
                    end = min(i + batch_size, final_size)
                    batch_size_actual = end - i
                    added_indices = np.random.choice(minority_indices, batch_size_actual, replace=True)
                    X_memmap[i:end] = X_memmap[added_indices] + np.random.randn(batch_size_actual, n_features) * 0.1
                    y_memmap[i:end] = 1
                    if i % (batch_size * 10) == 0:
                        print(f"  Added {end - (n_normal + n_fraud):,} / {n_to_add:,} SMOTE samples...")
        
        # Scale data
        print("Scaling data...")
        sample_idx = np.random.choice(final_size, min(100000, final_size), replace=False)
        scaler = StandardScaler()
        scaler.fit(X_memmap[sample_idx])
        
        for i in range(0, final_size, batch_size):
            end = min(i + batch_size, final_size)
            X_memmap[i:end] = scaler.transform(X_memmap[i:end])
            if i % (batch_size * 10) == 0:
                print(f"  Scaled {end:,} / {final_size:,} samples...")
        
        # Keep as memmap arrays (don't load into memory)
        print(f"Data stored in memory-mapped files: {X_file}, {y_file}")
        print(f"Generated {n_samples:,} samples, Final: {final_size:,} samples")
        print(f"Fraud rate: {np.mean(y_memmap)*100:.2f}% (target: {target_fraud_rate*100:.2f}%)")
        
        # Return memmap arrays with file info for cleanup
        return X_memmap, y_memmap, (X_file, y_file)
        
    else:
        # Small dataset - generate all at once
        X_normal = np.random.randn(n_normal, n_features) * 0.8
        X_fraud = np.random.randn(n_fraud, n_features) * 0.8
        X_fraud[:, 0] += 3.0
        X_fraud[:, 1] += 2.5
        X_fraud[:, 2] -= 2.0
        X_fraud[:, 3] += 2.0
        X_fraud[:, 4] += 1.5
        
        X = np.vstack([X_normal, X_fraud])
        y = np.hstack([np.zeros(n_normal), np.ones(n_fraud)])
        
        # Shuffle
        idx = np.random.permutation(len(X))
        X, y = X[idx], y[idx]
        
        # Apply SMOTE
        current_fraud_rate = np.mean(y)
        if current_fraud_rate < target_fraud_rate:
            n_minority = int(np.sum(y == 1))
            n_majority = int(np.sum(y == 0))
            target_minority = int(n_majority * target_fraud_rate / (1 - target_fraud_rate))
            
            sampling_strategy = {1: target_minority}
            smote = SMOTE(sampling_strategy=sampling_strategy, random_state=42)
            X_resampled, y_resampled = smote.fit_resample(X, y)
            X, y = X_resampled, y_resampled
        
        # Scale
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        
        print(f"Generated {n_samples:,} samples, Final: {len(X):,} samples")
        print(f"Fraud rate: {np.mean(y)*100:.2f}% (target: {target_fraud_rate*100:.2f}%)")
        return X, y, None


def create_clients(X, y, n_clients=8):
    np.random.seed(42)
    clients = []
    samples_per_client = len(X) // n_clients
    
    for cid in range(n_clients):
        start = cid * samples_per_client
        end = (cid + 1) * samples_per_client if cid < n_clients - 1 else len(X)
        
        # Copy client data (this is the memory bottleneck for large datasets)
        X_c = np.array(X[start:end])
        y_c = np.array(y[start:end])
        
        if len(np.unique(y_c)) < 2:
            missing = 0 if np.mean(y_c) > 0.5 else 1
            missing_idx = np.where(y == missing)[0]
            if len(missing_idx) > 0:
                add = np.random.choice(missing_idx, min(20, len(missing_idx)), replace=False)
                X_c = np.vstack([X_c, X[add]])
                y_c = np.hstack([y_c, y[add]])
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_c, y_c, test_size=0.2, random_state=cid, stratify=y_c
        )
        
        fraud_rate = np.mean(y_train) * 100
        print(f"Client {cid:2d}: Train={len(X_train):4d}, Test={len(X_test):4d}, Fraud={fraud_rate:.2f}%")
        clients.append((X_train, y_train, X_test, y_test))
    
    return clients


def generate_healthcare_ehr_data(n_samples=30000, disease_rate=0.02):
    """
    Simulate Electronic Health Records (EHR) for disease prediction
    Features: age, blood pressure, cholesterol, glucose, BMI, etc.
    """
    np.random.seed(42)
    n_features = 25
    
    # Generate normal patients
    n_normal = int(n_samples * (1 - disease_rate))
    n_disease = n_samples - n_normal
    
    X_normal = np.random.randn(n_normal, n_features) * 0.6
    # Add realistic correlations for normal patients
    X_normal[:, 0] = np.random.normal(45, 15, n_normal)  # Age
    X_normal[:, 1] = np.random.normal(120, 20, n_normal)  # Systolic BP
    X_normal[:, 2] = np.random.normal(80, 15, n_normal)   # Diastolic BP
    X_normal[:, 3] = np.random.normal(200, 40, n_normal)  # Cholesterol
    X_normal[:, 4] = np.random.normal(100, 30, n_normal)  # Glucose
    X_normal[:, 5] = np.random.normal(25, 5, n_normal)    # BMI
    
    # Generate disease patients with different patterns
    X_disease = np.random.randn(n_disease, n_features) * 0.6
    X_disease[:, 0] = np.random.normal(55, 12, n_disease)  # Higher age
    X_disease[:, 1] = np.random.normal(140, 25, n_disease)  # Higher BP
    X_disease[:, 2] = np.random.normal(90, 18, n_disease)   # Higher BP
    X_disease[:, 3] = np.random.normal(240, 50, n_disease)  # Higher cholesterol
    X_disease[:, 4] = np.random.normal(140, 40, n_disease)  # Higher glucose
    X_disease[:, 5] = np.random.normal(30, 6, n_disease)    # Higher BMI
    
    X = np.vstack([X_normal, X_disease])
    y = np.hstack([np.zeros(n_normal), np.ones(n_disease)])
    
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    print(f"Generated {n_samples:,} EHR samples, Disease rate: {np.mean(y)*100:.2f}%")
    return X, y


def generate_iot_anomaly_data(n_samples=30000, anomaly_rate=0.01):
    """
    Simulate IoT sensor data for anomaly detection
    Features: temperature, pressure, humidity, vibration, power consumption, etc.
    """
    np.random.seed(42)
    n_features = 30
    
    # Generate normal sensor readings
    n_normal = int(n_samples * (1 - anomaly_rate))
    n_anomaly = n_samples - n_normal
    
    X_normal = np.random.randn(n_normal, n_features) * 0.8
    # Add realistic sensor patterns with high overlap
    for i in range(n_features):
        base = np.random.uniform(0, 100)
        noise = np.random.normal(0, 25, n_normal)  # High noise for realism
        X_normal[:, i] = base + noise
    
    # Generate anomalies with very subtle deviations (very hard to detect)
    X_anomaly = np.random.randn(n_anomaly, n_features) * 0.8
    for i in range(n_features):
        base = np.random.uniform(0, 100)
        # Anomalies have very small deviations (high overlap with normal)
        anomaly_noise = np.random.choice([-1, 1], n_anomaly) * np.random.uniform(2, 8, n_anomaly)
        X_anomaly[:, i] = base + anomaly_noise
    
    X = np.vstack([X_normal, X_anomaly])
    y = np.hstack([np.zeros(n_normal), np.ones(n_anomaly)])
    
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    print(f"Generated {n_samples:,} IoT samples, Anomaly rate: {np.mean(y)*100:.2f}%")
    return X, y


def generate_recommender_data(n_samples=30000, fraud_rate=0.015):
    """
    Simulate recommender system data for fake review detection
    Features: rating frequency, text similarity, temporal patterns, user age, etc.
    """
    np.random.seed(42)
    n_features = 20
    
    # Generate legitimate reviews
    n_legit = int(n_samples * (1 - fraud_rate))
    n_fraud = n_samples - n_legit
    
    X_legit = np.random.randn(n_legit, n_features) * 0.7
    # Legitimate review patterns with more overlap
    X_legit[:, 0] = np.random.normal(3.5, 1.5, n_legit)  # Average rating (more variance)
    X_legit[:, 1] = np.random.normal(10, 15, n_legit)     # Review frequency (more overlap)
    X_legit[:, 2] = np.random.normal(0.3, 0.3, n_legit)   # Text similarity (more overlap)
    X_legit[:, 3] = np.random.normal(100, 80, n_legit)    # Account age (more overlap)
    X_legit[:, 4] = np.random.normal(0.1, 0.15, n_legit) # Burstiness (more overlap)
    
    # Generate fraudulent reviews with more subtle patterns
    X_fraud = np.random.randn(n_fraud, n_features) * 0.7
    # Fraudulent review patterns (less extreme, more overlap with legitimate)
    X_fraud[:, 0] = np.random.normal(4.2, 1.0, n_fraud)   # Moderately inflated ratings
    X_fraud[:, 1] = np.random.normal(25, 20, n_fraud)     # Moderately high frequency
    X_fraud[:, 2] = np.random.normal(0.5, 0.25, n_fraud)  # Moderately high similarity
    X_fraud[:, 3] = np.random.normal(20, 25, n_fraud)     # Moderately new accounts
    X_fraud[:, 4] = np.random.normal(0.4, 0.2, n_fraud)   # Moderately high burstiness
    
    X = np.vstack([X_legit, X_fraud])
    y = np.hstack([np.zeros(n_legit), np.ones(n_fraud)])
    
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    print(f"Generated {n_samples:,} recommender samples, Fraud rate: {np.mean(y)*100:.2f}%")
    return X, y


def create_non_iid_clients_multi_domain(X, y, n_clients=8, domain='fraud'):
    """
    Create non-IID clients with domain-specific heterogeneity
    """
    np.random.seed(42)
    clients = []
    samples_per_client = len(X) // n_clients
    
    # Domain-specific heterogeneity
    if domain == 'fraud':
        alpha = 0.3  # High heterogeneity for fraud
    elif domain == 'healthcare':
        alpha = 0.4  # Medium heterogeneity for healthcare
    elif domain == 'iot':
        alpha = 0.2  # Very high heterogeneity for IoT
    elif domain == 'recommender':
        alpha = 0.35  # Medium-high heterogeneity for recommender
    else:
        alpha = 0.3
    
    for cid in range(n_clients):
        start = cid * samples_per_client
        end = (cid + 1) * samples_per_client if cid < n_clients - 1 else len(X)
        
        X_c = X[start:end].copy()
        y_c = y[start:end].copy()
        
        # Ensure each client has both classes
        if len(np.unique(y_c)) < 2:
            missing = 0 if np.mean(y_c) > 0.5 else 1
            missing_idx = np.where(y == missing)[0]
            if len(missing_idx) > 0:
                add = np.random.choice(missing_idx, min(20, len(missing_idx)), replace=False)
                X_c = np.vstack([X_c, X[add]])
                y_c = np.hstack([y_c, y[add]])
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_c, y_c, test_size=0.2, random_state=cid, stratify=y_c
        )
        
        class_rate = np.mean(y_train) * 100
        print(f"Client {cid:2d}: Train={len(X_train):4d}, Test={len(X_test):4d}, "
              f"Class Rate={class_rate:.2f}%")
        clients.append((X_train, y_train, X_test, y_test))
    
    return clients


def multi_domain_experiment():
    """Run experiments across multiple domains"""
    print("="*70)
    print("MULTI-DOMAIN EXPERIMENT")
    print("="*70)
    
    domains = {
        'fraud': ('Credit Card Fraud', generate_data, 0.005),
        'healthcare': ('Healthcare EHR', generate_healthcare_ehr_data, 0.02),
        'iot': ('IoT Anomaly', generate_iot_anomaly_data, 0.01),
        'recommender': ('Recommender System', generate_recommender_data, 0.015)
    }
    
    all_results = {}
    
    for domain_key, (domain_name, gen_func, rate) in domains.items():
        print(f"\n{'='*70}")
        print(f"Domain: {domain_name}")
        print(f"{'='*70}")
        
        # Generate data
        if domain_key == 'healthcare':
            X, y = gen_func(n_samples=30000, disease_rate=rate)
        elif domain_key == 'iot':
            X, y = gen_func(n_samples=30000, anomaly_rate=rate)
        elif domain_key == 'recommender':
            X, y = gen_func(n_samples=30000, fraud_rate=rate)
        else:
            X, y = gen_func(n_samples=30000, fraud_rate=rate)
        
        # Create clients
        client_data = create_non_iid_clients_multi_domain(X, y, n_clients=8, domain=domain_key)
        
        # Train DeSecureFed
        from main import DeSecureFedServer, Client, train_server
        server = DeSecureFedServer()
        server = train_server(server, client_data, n_rounds=25)
        metrics = server.evaluate()
        
        all_results[domain_key] = {
            'domain': domain_name,
            'accuracy': metrics['accuracy'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1': metrics['f1'],
            'auc': metrics['auc']
        }
    
    # Print summary
    print(f"\n{'='*70}")
    print("MULTI-DOMAIN RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"{'Domain':<20} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10} {'AUC':<10}")
    print("-"*70)
    
    for domain_key, r in all_results.items():
        print(f"{r['domain']:<20} {r['accuracy']*100:.2f}%     "
              f"{r['precision']*100:.2f}%     {r['recall']*100:.2f}%     "
              f"{r['f1']*100:.2f}%     {r['auc']:.3f}")
    
    # Save results
    import pandas as pd
    df = pd.DataFrame([{
        'Domain': r['domain'],
        'Accuracy (%)': r['accuracy'] * 100,
        'Precision (%)': r['precision'] * 100,
        'Recall (%)': r['recall'] * 100,
        'F1 Score (%)': r['f1'] * 100,
        'AUC': r['auc']
    } for r in all_results.values()])
    
    df.to_csv('multi_domain_results.csv', index=False)
    print("\n✅ Results saved to 'multi_domain_results.csv'")
    
    return all_results


if __name__ == "__main__":
    multi_domain_experiment()
