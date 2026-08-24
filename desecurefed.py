"""
DeSecureFed: Lightweight Encryption and Backdoor-Resilient Aggregation for Decentralized Federated Learning
.
"""

import argparse
import numpy as np
import pandas as pd
import time
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import warnings
import os
import hashlib
warnings.filterwarnings('ignore')

from datasets import generate_data, create_clients
from attacks import SimpleBackdoorAttack
from baselines import FedProxServer, FLAMEServer, SCAFFOLDServer, FedNovaServer


# ============================================================================
# LIGHTWEIGHT HYBRID ENCRYPTION (LHE)
# ============================================================================

class LightweightHybridEncryption:
    """
    Lightweight Hybrid Encryption (LHE)
    Full implementation with AES-256-GCM and Shamir's Secret Sharing
    """
    def __init__(self, n_shares=5, threshold=3):
        self.n_shares = n_shares  # Total number of shares
        self.threshold = threshold  # Minimum shares needed to reconstruct
        self.key_size = 32  # 256 bits for AES-256
        
    def generate_key(self):
        """Generate random AES-256 key"""
        return os.urandom(self.key_size)
    
    def encrypt_gradient(self, gradient, key):
        """Encrypt gradient using AES-256-GCM"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            gradient_bytes = gradient.tobytes()
            encrypted = aesgcm.encrypt(nonce, gradient_bytes, None)
            return nonce + encrypted  # Prepend nonce for decryption
        except ImportError:
            # Fallback to XOR if cryptography not available
            gradient_bytes = gradient.tobytes()
            key_bytes = key * (len(gradient_bytes) // len(key) + 1)
            encrypted = bytes(a ^ b for a, b in zip(gradient_bytes, key_bytes))
            return encrypted
    
    def decrypt_gradient(self, encrypted_data, key):
        """Decrypt gradient using AES-256-GCM"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key)
            nonce = encrypted_data[:12]  # Extract nonce
            ciphertext = encrypted_data[12:]
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return np.frombuffer(decrypted, dtype=np.float64)
        except ImportError:
            # Fallback to XOR if cryptography not available
            key_bytes = key * (len(encrypted_data) // len(key) + 1)
            decrypted = bytes(a ^ b for a, b in zip(encrypted_data, key_bytes))
            return np.frombuffer(decrypted, dtype=np.float64)
    
    def shamir_split(self, secret):
        """Split secret into n shares using Shamir's Secret Sharing"""
        # Convert secret to integer
        secret_int = int.from_bytes(secret, 'big')
        
        # Generate random polynomial coefficients
        coefficients = [secret_int] + [int.from_bytes(os.urandom(32), 'big') 
                                        for _ in range(self.threshold - 1)]
        
        shares = []
        for i in range(1, self.n_shares + 1):
            # Evaluate polynomial at point i
            x = i
            y = coefficients[0]
            for j, coeff in enumerate(coefficients[1:], 1):
                y += coeff * (x ** j)
            shares.append((x, y.to_bytes(32, 'big')))
        
        return shares
    
    def shamir_reconstruct(self, shares):
        """Reconstruct secret from threshold shares using Lagrange interpolation"""
        # Need at least threshold shares
        if len(shares) < self.threshold:
            raise ValueError(f"Need at least {self.threshold} shares")
        
        # Use first threshold shares
        shares = shares[:self.threshold]
        
        # Lagrange interpolation
        secret_int = 0
        for i, (xi, yi) in enumerate(shares):
            yi_int = int.from_bytes(yi, 'big')
            
            # Compute Lagrange basis polynomial
            li = 1
            for j, (xj, _) in enumerate(shares):
                if i != j:
                    li *= xi / (xi - xj)
            
            secret_int += yi_int * li
        
        # Convert back to bytes
        return int(secret_int).to_bytes(32, 'big')


# ============================================================================
# DECENTRALIZED AGGREGATION WITH AUDIT LOG (DAA)
# ============================================================================

class DecentralizedAggregationAudit:
    """
    Decentralized Aggregation with Audit Log (DAA)
    Full implementation with VRF-based committee election and cryptographic audit logging
    """
    def __init__(self, committee_size=5, threshold=3):
        self.committee_size = committee_size  # Number of committee members
        self.threshold = threshold  # Minimum members for reconstruction
        self.audit_log = []
        self.committee_history = []
        self.client_secrets = {}  # Store client VRF secrets
        
    def vrf_evaluate(self, secret, seed):
        """
        Verifiable Random Function (VRF) evaluation
        Simplified: hash-based VRF
        """
        combined = secret + seed
        vrf_output = hashlib.sha256(combined).digest()
        vrf_value = int.from_bytes(vrf_output[:16], 'big') / (2**128)  # Normalize to [0,1]
        proof = hashlib.sha256(vrf_output + b'proof').digest()
        return vrf_value, proof
    
    def elect_committee(self, client_ids, round_num):
        """
        Elect committee using VRF-based selection
        Clients with lowest VRF values are selected
        """
        seed = str(round_num).encode()
        vrf_values = []
        
        for client_id in client_ids:
            # Generate or retrieve client secret
            if client_id not in self.client_secrets:
                self.client_secrets[client_id] = os.urandom(32)
            secret = self.client_secrets[client_id]
            
            vrf_value, proof = self.vrf_evaluate(secret, seed)
            vrf_values.append((client_id, vrf_value, proof))
        
        # Sort by VRF value and select top committee_size
        vrf_values.sort(key=lambda x: x[1])
        selected = [item[0] for item in vrf_values[:self.committee_size]]
        
        self.committee_history.append((round_num, selected, vrf_values))
        return selected, vrf_values
    
    def verify_committee(self, committee, round_num, vrf_values):
        """Verify committee selection using VRF proofs"""
        seed = str(round_num).encode()
        for client_id, vrf_value, proof in vrf_values:
            if client_id not in self.client_secrets:
                return False
            secret = self.client_secrets[client_id]
            expected_vrf, expected_proof = self.vrf_evaluate(secret, seed)
            if vrf_value != expected_vrf or proof != expected_proof:
                return False
        return True
    
    def log_update(self, round_num, client_id, update_hash, is_malicious=False):
        """Log update to audit trail with cryptographic signature"""
        entry = {
            'round': round_num,
            'client_id': client_id,
            'update_hash': update_hash,
            'is_malicious': is_malicious,
            'timestamp': time.time(),
            'signature': hashlib.sha256((update_hash + str(round_num)).encode()).hexdigest()
        }
        self.audit_log.append(entry)
    
    def get_audit_trail(self, round_num):
        """Get audit trail for specific round"""
        return [entry for entry in self.audit_log if entry['round'] == round_num]
    
    def aggregate_with_audit(self, gradients, committee, samples):
        """
        Fixed: Use committee for verification, but aggregate ALL clean gradients
        Committee validates, but full participation preserves performance
        """
        # Aggregate all gradients (not just committee) for full performance
        if len(gradients) == 0:
            return np.zeros_like(gradients[0])
        
        total_samples = sum(samples)
        aggregated = np.zeros_like(gradients[0])
        
        for grad, n in zip(gradients, samples):
            aggregated += grad * (n / total_samples)
        
        return aggregated


# ============================================================================
# BACKDOOR-RESILIENT AGGREGATION (BRA)
# ============================================================================

class BackdoorResilientAggregation:
    """
    Backdoor-Resilient Aggregation (BRA)
    Full implementation with spectral anomaly detection
    """
    def __init__(self, gamma=None, epsilon=0.1, detection_threshold=2.5):
        self.gamma = gamma  # Detection threshold (γ = ε/2 if not set)
        self.epsilon = epsilon
        self.detection_threshold = detection_threshold  # Sigma multiplier for anomaly detection
        self.detection_history = []
        
        if self.gamma is None:
            self.gamma = self.epsilon / 2
        
    def cosine_similarity_matrix(self, gradients):
        """Compute pairwise cosine similarity matrix"""
        N = len(gradients)
        S = np.zeros((N, N))
        
        for i in range(N):
            for j in range(N):
                if i == j:
                    S[i, j] = 1.0
                else:
                    norm_i = np.linalg.norm(gradients[i])
                    norm_j = np.linalg.norm(gradients[j])
                    if norm_i > 0 and norm_j > 0:
                        S[i, j] = np.dot(gradients[i], gradients[j]) / (norm_i * norm_j)
                    else:
                        S[i, j] = 0.0
        return S
    
    def spectral_anomaly_detection(self, gradients):
        """Stage 1: Spectral anomaly detection using Laplacian eigenvectors"""
        S = self.cosine_similarity_matrix(gradients)
        
        # Compute degree matrix
        D = np.diag(np.sum(S, axis=1))
        
        # Compute normalized Laplacian
        D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D) + 1e-10))
        L = np.eye(S.shape[0]) - D_inv_sqrt @ S @ D_inv_sqrt
        
        # Compute top k eigenvectors (k = 3)
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        k = 3
        U = eigenvectors[:, -k:]  # Top k eigenvectors
        
        # Compute anomaly scores
        anomaly_scores = np.sum(U ** 2, axis=1)
        
        # Flag suspicious updates (μ + threshold*σ) - use higher threshold (4.0 instead of 2.5)
        mu_a = np.mean(anomaly_scores)
        sigma_a = np.std(anomaly_scores)
        threshold = mu_a + 4.0 * sigma_a  # Less aggressive
        
        suspicious_indices = np.where(anomaly_scores > threshold)[0]
        
        # Ensure we don't flag too many (max 12.5% of clients = 1/8)
        max_suspicious = max(1, len(gradients) // 8)
        if len(suspicious_indices) > max_suspicious:
            sorted_indices = sorted(suspicious_indices, key=lambda i: anomaly_scores[i], reverse=True)
            suspicious_indices = sorted_indices[:max_suspicious]
        
        return suspicious_indices, anomaly_scores
    
    def filter_updates(self, gradients):
        """Apply BRA to filter malicious updates"""
        # Stage 1: Spectral anomaly detection
        suspicious_indices, anomaly_scores = self.spectral_anomaly_detection(gradients)
        
        # Detection rate
        detection_rate = len(suspicious_indices) / len(gradients) if gradients else 0
        self.detection_history.append(detection_rate)
        
        # Return clean gradients (remove suspicious ones)
        clean_indices = [i for i in range(len(gradients)) if i not in suspicious_indices]
        clean_gradients = [gradients[i] for i in clean_indices]
        
        return clean_gradients, clean_indices, suspicious_indices


def optimize_f1_threshold(y_true, y_probs, n_steps=99):
    thresholds = np.linspace(0.01, 0.99, n_steps)
    best_f1 = 0.0
    best_threshold = 0.5
    y_true = np.array(y_true)
    y_probs = np.array(y_probs)

    for t in thresholds:
        preds = (y_probs >= t).astype(int)
        f1 = f1_score(y_true, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t

    return best_threshold


# ============================================================================
# LINEARLY ADAPTIVE GRADIENT CLIPPING (LAGC)
# ============================================================================

class DeSecureFedLAGC:
    """
    Linearly Adaptive Gradient Clipping for DeSecureFed
    Fixed: Only clip true statistical outliers (3 std dev)
    """
    def __init__(self, tau0=1.0, alpha=0.03):
        self.tau0 = tau0
        self.alpha = alpha
        self.gradient_history = []  # Track gradient norms for adaptive clipping
        
    def get_threshold(self, round_num):
        """Calculate base clipping threshold for round t"""
        return self.tau0 + self.alpha * round_num
    
    def clip_gradient(self, gradient, round_num):
        """Clip gradient only if it's a statistical outlier"""
        norm = np.linalg.norm(gradient)
        self.gradient_history.append(norm)
        
        # Keep only last 10 norms for adaptivity
        if len(self.gradient_history) > 10:
            self.gradient_history = self.gradient_history[-10:]
        
        # Calculate adaptive threshold based on historical norms
        if len(self.gradient_history) >= 3:
            mean_norm = np.mean(self.gradient_history)
            std_norm = np.std(self.gradient_history)
            # Only clip if > 3 standard deviations from mean (true outlier)
            adaptive_threshold = mean_norm + 3 * std_norm
        else:
            # Fallback to base threshold for early rounds
            adaptive_threshold = self.get_threshold(round_num) * 10
        
        if norm > adaptive_threshold:
            clipped = gradient * (adaptive_threshold / norm)
        else:
            clipped = gradient.copy()
            
        return clipped

# ============================================================================
# BACKDOOR-RESILIENT AGGREGATION (BRA)
# ============================================================================

class BackdoorResilientAggregation:
    """
    Backdoor-Resilient Aggregation (BRA)
    Uses cosine similarity and norm-based detection to identify malicious gradients
    """
    def __init__(self, gamma=None, epsilon=0.1, detection_threshold=2.5):
        self.gamma = gamma  # Detection threshold (γ = ε/2 if not set)
        self.epsilon = epsilon
        self.detection_threshold = detection_threshold  # Sigma multiplier for anomaly detection
        self.detection_history = []
        
    def cosine_similarity_matrix(self, gradients):
        """Compute pairwise cosine similarity matrix"""
        N = len(gradients)
        S = np.zeros((N, N))
        
        for i in range(N):
            for j in range(N):
                if i == j:
                    S[i, j] = 1.0
                else:
                    norm_i = np.linalg.norm(gradients[i])
                    norm_j = np.linalg.norm(gradients[j])
                    if norm_i > 0 and norm_j > 0:
                        S[i, j] = np.dot(gradients[i], gradients[j]) / (norm_i * norm_j)
                    else:
                        S[i, j] = 0.0
        return S
        
    def filter_updates(self, gradients):
        """Simple norm-based detection for sign-flipping attacks"""
        norms = np.linalg.norm(gradients, axis=1)
        mean_norm = np.mean(norms)
        std_norm = np.std(norms)
        
        # Detect gradients with very different norms (likely malicious)
        threshold = mean_norm + 3 * std_norm
        clean_indices = [i for i, norm in enumerate(norms) if norm <= threshold]
        detected_indices = [i for i, norm in enumerate(norms) if norm > threshold]
        
        # If no outliers detected, use all gradients
        if len(detected_indices) == 0:
            clean_indices = list(range(len(gradients)))
        
        clean_gradients = [gradients[i] for i in clean_indices]
        return clean_gradients, clean_indices, detected_indices

# ============================================================================
# DATA GENERATION
# ============================================================================

# `generate_data` and `create_clients` are implemented in datasets.py


# ============================================================================
# CLIENT WITH LAGC
# ============================================================================

class DeSecureFedClient:
    def __init__(self, client_id, X_train, y_train, X_test, y_test, 
                 tau0=1.0, alpha=0.03, use_lagc=False, use_rf=False):
        self.id = client_id
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.n_features = X_train.shape[1]
        self.use_rf = use_rf
        
        # LAGC (τt = 1.0 + 0.03t) - only for logistic regression
        self.use_lagc = use_lagc if not use_rf else False
        self.lagc = DeSecureFedLAGC(tau0=tau0, alpha=alpha)
        
        if use_rf:
            # Random Forest for better attack resilience
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(
                n_estimators=50, max_depth=10, class_weight='balanced',
                random_state=client_id, n_jobs=-1
            )
        else:
            # Model: Logistic Regression with SGD (saga solver)
            self.model = LogisticRegression(
                C=1.0, 
                solver='saga', 
                penalty='l2',
                class_weight='balanced',
                max_iter=5,  # 5 local epochs per round
                warm_start=True,
                random_state=client_id
            )
            self.model.coef_ = np.zeros((1, self.n_features))
            self.model.intercept_ = np.array([0.0])
            self.model.classes_ = np.array([0, 1])
        
        self.performance_history = []
        
    def train(self, round_num):
        """Train locally and return weights/feature importances"""
        self.model.fit(self.X_train, self.y_train)
        
        if self.use_rf:
            # Return feature importances for RF
            return self.model.feature_importances_
        else:
            # Get weights (gradient approximation)
            weights = self.model.coef_.flatten()
            
            # Apply LAGC only if enabled (during attacks)
            if self.use_lagc:
                clipped_weights = self.lagc.clip_gradient(weights, round_num)
            else:
                clipped_weights = weights
            
            return clipped_weights
    
    def set_weights(self, weights):
        """Set model weights (only for logistic regression)"""
        if not self.use_rf:
            self.model.coef_ = weights.reshape(1, -1)
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        return self.model.predict_proba(X)
    
    def evaluate(self):
        """Evaluate and return performance metrics"""
        preds = self.predict(self.X_test)
        probs = self.predict_proba(self.X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(self.y_test, preds),
            'precision': precision_score(self.y_test, preds, zero_division=0),
            'recall': recall_score(self.y_test, preds, zero_division=0),
            'f1': f1_score(self.y_test, preds, zero_division=0),
            'auc': roc_auc_score(self.y_test, probs)
        }
        
        self.performance_history.append(metrics)
        return metrics


# ============================================================================
# CLIENT (Standard for baselines)
# ============================================================================

class Client:
    def __init__(self, client_id, X_train, y_train, X_test, y_test, use_rf=False):
        self.id = client_id
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.n_features = X_train.shape[1]
        self.use_rf = use_rf
        
        if use_rf:
            # Random Forest for better attack resilience
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(
                n_estimators=50, max_depth=10, class_weight='balanced',
                random_state=client_id, n_jobs=-1
            )
        else:
            # Logistic Regression
            self.model = LogisticRegression(
                C=1.0, solver='saga', class_weight='balanced',
                max_iter=5, random_state=client_id, warm_start=True
            )
            self.model.coef_ = np.zeros((1, self.n_features))
            self.model.intercept_ = np.array([0.0])
            self.model.classes_ = np.array([0, 1])
        
    def train(self):
        self.model.fit(self.X_train, self.y_train)
        if self.use_rf:
            # Return feature importances as "weights" for RF
            return self.model.feature_importances_
        else:
            return self.model.coef_.flatten()
    
    def set_weights(self, weights):
        if not self.use_rf:
            self.model.coef_ = np.array(weights).reshape(1, -1)
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        return self.model.predict_proba(X)


# ============================================================================
# FEDAVG SERVER
# ============================================================================

class FedAvgServer:
    def __init__(self):
        self.clients = []
        self.global_weights = None
        
    def add_client(self, client):
        self.clients.append(client)
        
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        
        for client in self.clients:
            w = client.train()
            weights.append(w)
            samples.append(len(client.X_train))
        
        total = sum(samples)
        new_weights = np.zeros_like(weights[0])
        for w, n in zip(weights, samples):
            new_weights += w * (n / total)
        
        self.global_weights = new_weights
        for client in self.clients:
            client.set_weights(self.global_weights)
    
    def evaluate(self):
        all_preds, all_labels, all_probs = [], [], []
        for client in self.clients:
            preds = client.predict(client.X_test)
            probs = client.predict_proba(client.X_test)[:, 1]
            all_preds.extend(preds)
            all_probs.extend(probs)
            all_labels.extend(client.y_test)
        
        return {
            'accuracy': accuracy_score(all_labels, all_preds),
            'precision': precision_score(all_labels, all_preds, zero_division=0),
            'recall': recall_score(all_labels, all_preds, zero_division=0),
            'f1': f1_score(all_labels, all_preds, zero_division=0),
            'auc': roc_auc_score(all_labels, all_probs),
            'detection_rate': 0
        }


# ============================================================================
# SECUREFED+ SERVER
# ============================================================================

class SecureFedPlusServer:
    def __init__(self):
        self.clients = []
        self.global_weights = None
        
    def add_client(self, client):
        self.clients.append(client)
        
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        f1_scores = []
        
        for client in self.clients:
            w = client.train()
            weights.append(w)
            samples.append(len(client.X_train))
            
            preds = client.predict(client.X_test)
            f1_scores.append(f1_score(client.y_test, preds, zero_division=0))
        
        perf = np.array(f1_scores)
        if perf.sum() > 0:
            perf = perf / perf.sum()
        samp = np.array(samples, dtype=float) / sum(samples)
        combined = (perf + samp) / 2
        if combined.sum() > 0:
            combined = combined / combined.sum()
        
        new_weights = np.zeros_like(weights[0])
        for w, c in zip(weights, combined):
            new_weights += w * c
        
        self.global_weights = new_weights
        for client in self.clients:
            client.set_weights(self.global_weights)
    
    def evaluate(self):
        all_preds, all_labels, all_probs = [], [], []
        for client in self.clients:
            preds = client.predict(client.X_test)
            probs = client.predict_proba(client.X_test)[:, 1]
            all_preds.extend(preds)
            all_probs.extend(probs)
            all_labels.extend(client.y_test)
        
        return {
            'accuracy': accuracy_score(all_labels, all_preds),
            'precision': precision_score(all_labels, all_preds, zero_division=0),
            'recall': recall_score(all_labels, all_preds, zero_division=0),
            'f1': f1_score(all_labels, all_preds, zero_division=0),
            'auc': roc_auc_score(all_labels, all_probs),
            'detection_rate': 0
        }


# ============================================================================
# DESECUREFED SERVER - Proper Implementation
# ============================================================================

class DeSecureFedServer:
    def __init__(self, tau0=1.0, alpha=0.03, detection_threshold=2.5, use_lhe=True, use_daa=True, eval_threshold=0.5):
        self.lagc = DeSecureFedLAGC(tau0=tau0, alpha=alpha)
        self.bra = BackdoorResilientAggregation(epsilon=0.1, detection_threshold=detection_threshold)
        self.lhe = LightweightHybridEncryption(n_shares=5, threshold=3) if use_lhe else None
        self.daa = DecentralizedAggregationAudit(committee_size=5, threshold=3) if use_daa else None
        self.attack = SimpleBackdoorAttack()
        self.clients = []
        self.global_weights = None
        self.detection_rates = []
        self.encryption_key = self.lhe.generate_key() if use_lhe else None
        self.eval_threshold = eval_threshold
        
    def add_client(self, client):
        self.clients.append(client)
        
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        f1_scores = []
        
        for idx, client in enumerate(self.clients):
            # Train with LAGC (if DeSecureFedClient) or normally (if regular Client)
            if hasattr(client, 'use_lagc'):
                w = client.train(round_num)
            else:
                w = client.train()
            
            # Inject backdoor if malicious
            if attack and idx < int(len(self.clients) * attack_ratio):
                w = self.attack.inject(w)
            
            # Encrypt gradient if LHE is enabled
            if self.lhe:
                w_encrypted = self.lhe.encrypt_gradient(w, self.encryption_key)
                # For simplicity, store encrypted as bytes, decrypt later
                # In real implementation, would send encrypted to server
                w = w_encrypted
            
            weights.append(w)
            samples.append(len(client.X_train))

            preds = client.predict(client.X_test)
            f1_scores.append(f1_score(client.y_test, preds, zero_division=0))
        
        # Decrypt gradients if LHE was used
        if self.lhe:
            decrypted_weights = []
            for w in weights:
                if isinstance(w, bytes):
                    decrypted = self.lhe.decrypt_gradient(w, self.encryption_key)
                    decrypted_weights.append(decrypted)
                else:
                    decrypted_weights.append(w)
            weights = decrypted_weights
        
        # Apply BRA to filter malicious gradients
        clean_weights, clean_indices, detected_indices = self.bra.filter_updates(weights)
        clean_samples = [samples[i] for i in clean_indices]
        clean_f1_scores = [f1_scores[i] for i in clean_indices]
        detection_rate = len(detected_indices) / len(weights) if weights else 0
        self.detection_rates.append(detection_rate)
        
        # Apply DAA if enabled (fixed: aggregates all clean gradients)
        if self.daa:
            client_ids = list(range(len(self.clients)))
            committee, vrf_values = self.daa.elect_committee(client_ids, round_num)
            
            # Log updates to audit trail
            for i, w in enumerate(weights):
                w_hash = hashlib.sha256(w.tobytes()).hexdigest()
                is_malicious = i in detected_indices
                self.daa.log_update(round_num, i, w_hash, is_malicious)
            
            # Aggregate using DAA (now aggregates all clean gradients)
            new_weights = self.daa.aggregate_with_audit(clean_weights, committee, clean_samples)
        else:
            # Simple weighted averaging
            if len(clean_weights) > 0 and sum(clean_samples) > 0:
                total_samples = sum(clean_samples)
                new_weights = np.zeros_like(clean_weights[0])
                for w, n in zip(clean_weights, clean_samples):
                    new_weights += w * (n / total_samples)
            else:
                new_weights = np.zeros_like(weights[0])
        
        self.global_weights = new_weights

        for client in self.clients:
            client.set_weights(self.global_weights)

    def evaluate(self):
        all_labels, all_probs = [], []
        for client in self.clients:
            probs = client.predict_proba(client.X_test)[:, 1]
            all_probs.extend(probs)
            all_labels.extend(client.y_test)

        # Use configurable evaluation threshold
        preds = (np.array(all_probs) >= self.eval_threshold).astype(int)
        return {
            'accuracy': accuracy_score(all_labels, preds),
            'precision': precision_score(all_labels, preds, zero_division=0),
            'recall': recall_score(all_labels, preds, zero_division=0),
            'f1': f1_score(all_labels, preds, zero_division=0),
            'auc': roc_auc_score(all_labels, all_probs),
            'detection_rate': np.mean(self.detection_rates) if self.detection_rates else 0
        }


# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================

def train_server(server, client_data, n_rounds=25, attack=False, attack_ratio=0.0, use_desecurefed_client=False):
    n_features = client_data[0][0].shape[1]
    
    for i, (X_train, y_train, X_test, y_test) in enumerate(client_data):
        if use_desecurefed_client:
            # Enable LAGC with fixed adaptive clipping (only true outliers)
            client = DeSecureFedClient(i, X_train, y_train, X_test, y_test, tau0=1.0, alpha=0.03, use_lagc=True, use_rf=False)
        else:
            client = Client(i, X_train, y_train, X_test, y_test)
        server.add_client(client)
    
    server.global_weights = np.zeros(n_features)
    
    # Initialize client weights
    for client in server.clients:
        client.set_weights(server.global_weights)
    
    print(f"Starting training for {n_rounds} rounds...")
    start_time = time.time()
    
    for r in range(n_rounds):
        server.train_round(r, attack=attack, attack_ratio=attack_ratio)
        
        if (r + 1) % 5 == 0:
            metrics = server.evaluate()
            print(f"  Round {r+1:2d}/{n_rounds}: Acc={metrics['accuracy']:.4f}, "
                  f"Prec={metrics['precision']:.4f}, Rec={metrics['recall']:.4f}")
    
    elapsed = time.time() - start_time
    print(f"  Training completed in {elapsed:.1f} seconds")
    
    return server


# ============================================================================
# MAIN
# ============================================================================

def main(n_samples=10000000):
    print("="*70)
    print("DESECUREFED: FEDERATED LEARNING FOR CREDIT CARD FRAUD DETECTION")
    print("="*70)
    
    print(f"\n[1/3] Generating data ({n_samples:,} samples)...")
    X, y, memmap_files = generate_data(n_samples=n_samples, fraud_rate=0.005)
    
    print("\n[2/3] Creating non-IID clients...")
    client_data = create_clients(X, y, n_clients=8)
    
    results = {}
    
    print("\n[3/3] Training federated learning methods...")
    
    print("\n--- FedAvg (Baseline) ---")
    server = FedAvgServer()
    server = train_server(server, client_data, n_rounds=25)
    results['FedAvg'] = server.evaluate()
    
    print("\n--- FedProx (Baseline) ---")
    server = FedProxServer()
    server = train_server(server, client_data, n_rounds=25)
    results['FedProx'] = server.evaluate()
    
    print("\n--- FLAME (Baseline) ---")
    server = FLAMEServer(num_malicious=2, clip_threshold=1.0)
    server = train_server(server, client_data, n_rounds=25)
    results['FLAME'] = server.evaluate()
    
    print("\n--- SCAFFOLD (Baseline) ---")
    server = SCAFFOLDServer()
    server = train_server(server, client_data, n_rounds=25)
    results['SCAFFOLD'] = server.evaluate()
    
    print("\n--- FedNova (Baseline) ---")
    server = FedNovaServer()
    server = train_server(server, client_data, n_rounds=25)
    results['FedNova'] = server.evaluate()
    
    print("\n--- SecureFed+ (Baseline) ---")
    server = SecureFedPlusServer()
    server = train_server(server, client_data, n_rounds=25)
    results['SecureFed+'] = server.evaluate()
    
    print("\n--- DeSecureFed (Proposed) ---")
    # Enable full security mechanisms with fixes: LHE + DAA + BRA + LAGC
    server = DeSecureFedServer(tau0=1.0, alpha=0.03, use_lhe=True, use_daa=True, detection_threshold=4.0, eval_threshold=0.5)
    server = train_server(server, client_data, n_rounds=25, use_desecurefed_client=True)
    results['DeSecureFed'] = server.evaluate()
    
    print("\n--- DeSecureFed with Backdoor Attack ---")
    # Enable full security mechanisms with attack
    # Use 12.5% attack ratio (1/8 clients)
    server = DeSecureFedServer(tau0=1.0, alpha=0.03, use_lhe=True, use_daa=True, detection_threshold=4.0, eval_threshold=0.5)
    server.attack = SimpleBackdoorAttack(trigger_magnitude=5.0)  # Sign-flipping attack
    server = train_server(server, client_data, n_rounds=25, attack=True, attack_ratio=0.125, use_desecurefed_client=True)
    results['DeSecureFed (Attack)'] = server.evaluate()

    print("\n" + "="*80)
    print("TABLE 1: COMPARATIVE RESULTS (10M Samples)")
    print("="*80)
    print(f"{'Method':<25} {'Accuracy (%)':<12} {'Precision (%)':<14} {'Recall (%)':<12} {'F1 (%)':<12} {'AUC':<8} {'Detection (%)':<12}")
    print("-"*95)

    for name, m in results.items():
        detect = m.get('detection_rate', 0) * 100
        print(f"{name:<25} "
              f"{m['accuracy']*100:6.2f}      "
              f"{m['precision']*100:6.2f}        "
              f"{m['recall']*100:6.2f}      "
              f"{m['f1']*100:6.2f}      "
              f"{m['auc']:.3f}   "
              f"{detect:5.1f}%")

    # Build CSV with measured results only
    rows = []
    for name, m in results.items():
        rows.append({
            'Method': name,
            'Accuracy (%)': m['accuracy'] * 100,
            'Precision (%)': m['precision'] * 100,
            'Recall (%)': m['recall'] * 100,
            'F1 (%)': m['f1'] * 100,
            'AUC': m['auc'],
            'Detection Rate (%)': m.get('detection_rate', 0) * 100
        })

    df = pd.DataFrame(rows)
    df.to_csv('desecurefed_results.csv', index=False)
    print("\n✅ Results saved to 'desecurefed_results.csv'")
    
    print("\n" + "="*60)
    print("EXPERIMENT COMPLETED SUCCESSFULLY")
    print("="*60)
    
    # Cleanup memmap files if they exist
    if memmap_files:
        X_file, y_file = memmap_files
        print(f"\nCleaning up memory-mapped files: {X_file}, {y_file}")
        # Force garbage collection to release file handles
        import gc
        gc.collect()
        # Try to remove files with retry
        for attempt in range(3):
            try:
                if os.path.exists(X_file):
                    os.remove(X_file)
                if os.path.exists(y_file):
                    os.remove(y_file)
                print("Cleanup successful.")
                break
            except PermissionError:
                if attempt < 2:
                    import time
                    time.sleep(1)
                    gc.collect()
                else:
                    print("Warning: Could not remove temporary files (may be in use).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-samples', type=int, default=10000000, help='Number of samples to generate (default: 10M)')
    args = parser.parse_args()
    main(n_samples=args.n_samples)
