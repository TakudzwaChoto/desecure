"""
DeSecureFed: Additional Baseline Methods
Implements FLAME, FedProx, and other recent FL frameworks
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score, roc_auc_score
from scipy.spatial.distance import cosine


class FedProxServer:
    """
    FedProx: Federated Optimization in Heterogeneous Networks
    Uses proximal term to handle data heterogeneity
    """
    def __init__(self, mu=0.1):
        self.clients = []
        self.global_weights = None
        self.mu = mu  # Proximal term coefficient
        self.detection_rates = []
        
    def add_client(self, client):
        self.clients.append(client)
        
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        
        for idx, client in enumerate(self.clients):
            w = client.train()
            
            # Inject backdoor if malicious
            if attack and idx < int(len(self.clients) * attack_ratio):
                w[:10] += 5.0
            
            weights.append(w)
            samples.append(len(client.X_train))
        
        # Standard FedAvg aggregation (proximal term is handled in local training)
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


class FLAMEServer:
    """
    FLAME: Taming Backdoors in Federated Learning
    Uses robust aggregation with clipping and Krum
    """
    def __init__(self, num_malicious=2, clip_threshold=1.0):
        self.clients = []
        self.global_weights = None
        self.num_malicious = num_malicious
        self.clip_threshold = clip_threshold
        self.detection_rates = []
        
    def add_client(self, client):
        self.clients.append(client)
        
    def _clip_gradient(self, gradient):
        """Clip gradient to threshold"""
        norm = np.linalg.norm(gradient)
        if norm > self.clip_threshold:
            gradient = gradient * (self.clip_threshold / norm)
        return gradient
    
    def _krum(self, gradients, num_malicious):
        """Krum robust aggregation"""
        n = len(gradients)
        if n <= num_malicious + 2:
            # Not enough clients for Krum, return average
            return np.mean(gradients, axis=0)
        
        scores = []
        
        for i, g_i in enumerate(gradients):
            distances = []
            for j, g_j in enumerate(gradients):
                if i != j:
                    dist = np.linalg.norm(g_i - g_j)
                    distances.append(dist)
            distances.sort()
            # Sum of n - f - 2 smallest distances
            score = sum(distances[:n - num_malicious - 2])
            scores.append(score)
        
        return gradients[np.argmin(scores)]
    
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        
        for idx, client in enumerate(self.clients):
            w = client.train()
            
            # Inject backdoor if malicious
            if attack and idx < int(len(self.clients) * attack_ratio):
                w[:10] += 5.0
            
            # Clip gradient ONLY during attack
            if attack:
                w = self._clip_gradient(w)
            
            weights.append(w)
            samples.append(len(client.X_train))
        
        # Use Krum for robust aggregation ONLY during attack
        if attack and len(weights) > self.num_malicious + 2:
            robust_weight = self._krum(weights, self.num_malicious)
            new_weights = robust_weight
        else:
            # Fallback to weighted average
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


class SCAFFOLDServer:
    """
    SCAFFOLD: Stochastic Controlled Averaging for Federated Learning
    Uses control variates to handle client heterogeneity
    """
    def __init__(self):
        self.clients = []
        self.global_weights = None
        self.global_control = None
        self.client_controls = []
        self.detection_rates = []
        
    def add_client(self, client):
        self.clients.append(client)
        self.client_controls.append(np.zeros_like(client.model.coef_.flatten()))
        
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        
        for idx, client in enumerate(self.clients):
            w = client.train()
            
            # Inject backdoor if malicious
            if attack and idx < int(len(self.clients) * attack_ratio):
                w[:10] += 5.0
            
            # Apply control variate correction
            corrected = w - self.client_controls[idx]
            weights.append(corrected)
            samples.append(len(client.X_train))
        
        # Aggregate
        total = sum(samples)
        new_weights = np.zeros_like(weights[0])
        for w, n in zip(weights, samples):
            new_weights += w * (n / total)
        
        # Update global control
        if self.global_control is None:
            self.global_control = np.zeros_like(new_weights)
        
        control_update = np.zeros_like(new_weights)
        for i, client in enumerate(self.clients):
            control_update += (weights[i] - new_weights) / len(self.clients)
        
        self.global_control += control_update
        
        # Update client controls
        for i in range(len(self.clients)):
            self.client_controls[i] += (weights[i] - new_weights) - self.global_control
        
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


class FedNovaServer:
    """
    FedNova: Tackling the Objective Inconsistency Problem
    Normalizes gradients by local training steps
    """
    def __init__(self):
        self.clients = []
        self.global_weights = None
        self.detection_rates = []
        
    def add_client(self, client):
        self.clients.append(client)
        
    def train_round(self, round_num, attack=False, attack_ratio=0.0):
        weights = []
        samples = []
        taus = []  # Normalization factors
        
        for idx, client in enumerate(self.clients):
            w = client.train()
            
            # Inject backdoor if malicious
            if attack and idx < int(len(self.clients) * attack_ratio):
                w[:10] += 5.0
            
            weights.append(w)
            samples.append(len(client.X_train))
            taus.append(1.0)  # Assume 1 epoch per round
        
        # FedNova aggregation with normalization
        total_samples = sum(samples)
        new_weights = np.zeros_like(weights[0])
        
        for w, n, tau in zip(weights, samples, taus):
            # Normalize by local steps
            normalized = w / tau
            new_weights += normalized * (n / total_samples)
        
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


# Import metrics
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
