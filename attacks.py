"""
DeSecureFed: Advanced Backdoor Attack Models
Implements adaptive and sophisticated backdoor attacks
"""

import numpy as np
from scipy.spatial.distance import cosine
from sklearn.cluster import KMeans


class SimpleBackdoorAttack:
    """Basic backdoor attack with fixed trigger pattern"""
    def __init__(self, trigger_magnitude=5.0, trigger_indices=None):
        self.trigger_magnitude = trigger_magnitude
        self.trigger_indices = trigger_indices
        
    def inject(self, gradient):
        """Inject backdoor into gradient - flip signs to cause model divergence"""
        poisoned = gradient.copy()
        # Flip signs on all gradients to maximize damage
        poisoned = -poisoned
        # Add trigger pattern
        indices = self.trigger_indices if self.trigger_indices else list(range(min(10, len(poisoned))))
        for idx in indices:
            if idx < len(poisoned):
                poisoned[idx] += self.trigger_magnitude
        return poisoned


class AdaptiveBackdoorAttack:
    """Adaptive backdoor that evades spectral detection"""
    def __init__(self, target_norm=None, evasion_strength=0.5):
        self.target_norm = target_norm
        self.evasion_strength = evasion_strength
        self.benign_gradients = []
        
    def observe_benign(self, gradients):
        """Learn from benign gradients to blend in"""
        self.benign_gradients.extend(gradients)
        if len(self.benign_gradients) > 100:
            self.benign_gradients = self.benign_gradients[-100:]
    
    def inject(self, gradient, round_num=0):
        """Inject adaptive backdoor"""
        poisoned = gradient.copy()
        
        # Add trigger pattern
        poisoned[:10] += 3.0
        
        # Adaptive normalization to match benign distribution
        if self.benign_gradients:
            benign_norms = [np.linalg.norm(g) for g in self.benign_gradients]
            target_norm = np.mean(benign_norms) if self.target_norm is None else self.target_norm
            
            current_norm = np.linalg.norm(poisoned)
            if current_norm > 0:
                # Blend between malicious and target norm
                blend_factor = min(self.evasion_strength, 1.0)
                new_norm = current_norm * (1 - blend_factor) + target_norm * blend_factor
                poisoned = poisoned * (new_norm / current_norm)
        
        # Gradually reduce attack strength over rounds to evade detection
        decay = max(0.3, 1.0 - round_num * 0.02)
        poisoned[:10] = poisoned[:10] * decay + gradient[:10] * (1 - decay)
        
        return poisoned


class SpectralEvasionAttack:
    """Backdoor attack designed to evade spectral anomaly detection"""
    def __init__(self, n_clusters=3, evasion_mode='blend'):
        self.n_clusters = n_clusters
        self.evasion_mode = evasion_mode
        self.benign_gradients = []
        self.cluster_centers = None
        
    def update_clusters(self, gradients):
        """Update cluster centers based on benign gradients"""
        self.benign_gradients.extend(gradients)
        if len(self.benign_gradients) >= self.n_clusters:
            X = np.array(self.benign_gradients)
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
            kmeans.fit(X)
            self.cluster_centers = kmeans.cluster_centers_
    
    def inject(self, gradient):
        """Inject backdoor that blends with benign clusters"""
        poisoned = gradient.copy()
        
        # Add trigger pattern
        poisoned[:10] += 4.0
        
        if self.cluster_centers is not None:
            if self.evasion_mode == 'blend':
                # Blend with nearest cluster center
                distances = [cosine(poisoned, center) for center in self.cluster_centers]
                nearest_center = self.cluster_centers[np.argmin(distances)]
                blend_factor = 0.3
                poisoned = poisoned * (1 - blend_factor) + nearest_center * blend_factor
            
            elif self.evasion_mode == 'project':
                # Project onto benign subspace
                X_benign = np.array(self.benign_gradients)
                U, s, Vt = np.linalg.svd(X_benign.T, full_matrices=False)
                k = min(5, len(s))
                U_k = U[:, :k]
                projection = U_k @ (U_k.T @ poisoned)
                poisoned = projection * 0.7 + poisoned * 0.3
        
        return poisoned


class GradientScalingAttack:
    """Attack that uses scaling to evade magnitude-based detection"""
    def __init__(self, scale_factors=None):
        self.scale_factors = scale_factors if scale_factors else [0.8, 1.0, 1.2]
        self.current_scale_idx = 0
        
    def inject(self, gradient):
        """Inject backdoor with varying scale"""
        poisoned = gradient.copy()
        
        # Add trigger pattern
        poisoned[:10] += 5.0
        
        # Apply scaling
        scale = self.scale_factors[self.current_scale_idx]
        self.current_scale_idx = (self.current_scale_idx + 1) % len(self.scale_factors)
        poisoned = poisoned * scale
        
        return poisoned


class SignFlippingAttack:
    """Attack that flips gradient signs to cause model divergence"""
    def __init__(self, flip_ratio=0.3):
        self.flip_ratio = flip_ratio
        
    def inject(self, gradient):
        """Inject sign-flipping backdoor"""
        poisoned = gradient.copy()
        
        # Flip signs on subset of dimensions
        n_flip = int(len(poisoned) * self.flip_ratio)
        flip_indices = np.random.choice(len(poisoned), n_flip, replace=False)
        poisoned[flip_indices] = -poisoned[flip_indices]
        
        # Add subtle trigger pattern
        poisoned[:5] += 2.0
        
        return poisoned


class MultiModalAttack:
    """Combines multiple attack strategies"""
    def __init__(self, attacks=None):
        self.attacks = attacks if attacks else [
            AdaptiveBackdoorAttack(),
            SpectralEvasionAttack(),
            GradientScalingAttack()
        ]
        self.current_attack_idx = 0
        
    def inject(self, gradient, round_num=0):
        """Rotate between different attack strategies"""
        attack = self.attacks[self.current_attack_idx]
        
        if hasattr(attack, 'inject'):
            poisoned = attack.inject(gradient, round_num)
        else:
            poisoned = attack.inject(gradient)
        
        self.current_attack_idx = (self.current_attack_idx + 1) % len(self.attacks)
        return poisoned


class BackdoorAttackManager:
    """Manages multiple backdoor attack strategies"""
    def __init__(self, attack_type='adaptive', **kwargs):
        self.attack_type = attack_type
        self.kwargs = kwargs
        self.attack = self._create_attack()
        self.attack_history = []
        
    def _create_attack(self):
        if self.attack_type == 'simple':
            return SimpleBackdoorAttack(**self.kwargs)
        elif self.attack_type == 'adaptive':
            return AdaptiveBackdoorAttack(**self.kwargs)
        elif self.attack_type == 'spectral':
            return SpectralEvasionAttack(**self.kwargs)
        elif self.attack_type == 'scaling':
            return GradientScalingAttack(**self.kwargs)
        elif self.attack_type == 'sign_flip':
            return SignFlippingAttack(**self.kwargs)
        elif self.attack_type == 'multimodal':
            return MultiModalAttack(**self.kwargs)
        else:
            raise ValueError(f"Unknown attack type: {self.attack_type}")
    
    def observe(self, gradients):
        """Allow attack to observe benign gradients"""
        if hasattr(self.attack, 'observe_benign'):
            self.attack.observe_benign(gradients)
        if hasattr(self.attack, 'update_clusters'):
            self.attack.update_clusters(gradients)
    
    def inject(self, gradient, round_num=0):
        """Inject backdoor into gradient"""
        poisoned = self.attack.inject(gradient, round_num)
        self.attack_history.append(poisoned.copy())
        return poisoned
    
    def get_statistics(self):
        """Get attack statistics"""
        if not self.attack_history:
            return {}
        
        norms = [np.linalg.norm(g) for g in self.attack_history]
        return {
            'mean_norm': np.mean(norms),
            'std_norm': np.std(norms),
            'min_norm': np.min(norms),
            'max_norm': np.max(norms),
            'num_attacks': len(self.attack_history)
        }
