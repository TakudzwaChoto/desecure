import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'figure.figsize': (8, 5),
    'lines.linewidth': 2,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'legend.frameon': True,
    'legend.fancybox': True,
    'legend.shadow': True,
})

methods = ['FedAvg', 'FedProx', 'FLAME', 'SCAFFOLD', 
           'FedNova', 'SecureFed+', 'DeSecureFed']
accuracy = [99.48, 99.48, 99.48, 99.48, 99.48, 99.76, 99.96]
precision = [79.46, 79.46, 79.46, 79.46, 79.46, 89.20, 98.29]
recall = [99.96, 99.96, 99.96, 99.96, 99.96, 99.98, 99.71]
f1 = [88.54, 88.54, 88.54, 88.54, 88.54, 94.28, 98.99]

attack_scenarios = ['No Attack', '12.5% Attack']
attack_accuracy = [99.96, 99.61]
attack_precision = [98.29, 83.71]
attack_recall = [99.71, 99.99]
attack_f1 = [98.99, 91.13]

clients = [10, 20, 50, 100]
desecurefed_scalability = [99.9, 99.8, 99.7, 99.5]
securefed_scalability = [99.8, 99.7, 99.5, 99.1]
fedavg_scalability = [99.8, 99.7, 99.4, 99.0]

training_methods = ['FedAvg', 'SecureFed+', 'DeSecureFed']
training_times = [821.1, 853.6, 812.1]

dimensions = [1000, 5000, 10000, 50000]
desecurefed_latency = [5.2, 21.8, 41.2, 198.5]
securefed_latency = [23.4, 98.7, 187.3, 892.1]


def figure_accuracy_f1():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(methods))
    width = 0.35
    
    colors_acc = ['#4A90A4'] * len(methods)
    colors_acc[-1] = '#C0392B'
    colors_f1 = ['#F39C12'] * len(methods)
    colors_f1[-1] = '#C0392B'
    
    bars1 = ax.bar(x - width/2, accuracy, width, label='Accuracy', 
                   color=colors_acc, edgecolor='#2C3E50', linewidth=1.2)
    bars2 = ax.bar(x + width/2, f1, width, label='F1 Score', 
                   color=colors_f1, edgecolor='#2C3E50', linewidth=1.2)
    
    for i, bar in enumerate(bars1):
        if i == len(bars1) - 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{bar.get_height():.2f}', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color='#C0392B')
    
    for i, bar in enumerate(bars2):
        if i == len(bars2) - 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{bar.get_height():.2f}', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color='#C0392B')
    
    ax.set_ylabel('Performance Metric (%)', fontsize=13, fontweight='bold')
    ax.set_ylim(70, 102)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=30, ha='right', fontsize=10)
    ax.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True, 
              title='Red bars: DeSecureFed (Proposed)')
    ax.grid(True, alpha=0.25, linestyle='--', axis='y', linewidth=0.8)
    
    plt.tight_layout()
    plt.savefig('figure_accuracy_f1.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('figure_accuracy_f1.png', bbox_inches='tight', dpi=300)
    plt.show()
    print("✓ Accuracy and F1 Score figure generated")
    return fig

def figure_precision_recall():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(methods))
    width = 0.35
    
    colors_prec = ['#27AE60'] * len(methods)
    colors_prec[-1] = '#C0392B'
    colors_rec = ['#3498DB'] * len(methods)
    colors_rec[-1] = '#C0392B'
    
    bars1 = ax.bar(x - width/2, precision, width, label='Precision', 
                   color=colors_prec, edgecolor='#2C3E50', linewidth=1.2)
    bars2 = ax.bar(x + width/2, recall, width, label='Recall', 
                   color=colors_rec, edgecolor='#2C3E50', linewidth=1.2)
    
    for i, bar in enumerate(bars1):
        if i == len(bars1) - 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                    f'{bar.get_height():.2f}', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color='#C0392B')
    
    for i, bar in enumerate(bars2):
        if i == len(bars2) - 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 1.5,
                    f'{bar.get_height():.2f}', ha='center', va='top', 
                    fontsize=10, fontweight='bold', color='white')
    
    ax.set_ylabel('Performance Metric (%)', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=30, ha='right', fontsize=10)
    ax.legend(loc='lower left', fontsize=11, frameon=True, fancybox=True, shadow=True,
              title='Red bars: DeSecureFed (Proposed)')
    ax.grid(True, alpha=0.25, linestyle='--', axis='y', linewidth=0.8)
    
    plt.tight_layout()
    plt.savefig('figure_precision_recall.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('figure_precision_recall.png', bbox_inches='tight', dpi=300)
    plt.show()
    print("✓ Precision and Recall figure generated")
    return fig


def figure_encryption_latency():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.loglog(dimensions, desecurefed_latency, 'o-', linewidth=2.5, 
              markersize=10, label='DeSecureFed (LHE)', color='#4A90A4', 
              markerfacecolor='white', markeredgewidth=2)
    ax.loglog(dimensions, securefed_latency, 's-', linewidth=2.5, 
              markersize=10, label='SecureFed+ (Paillier)', color='#C0392B',
              markerfacecolor='white', markeredgewidth=2)
    
    ax.fill_between(dimensions, desecurefed_latency, securefed_latency, 
                     alpha=0.15, color='#C0392B')
    
    for d, l1, l2 in zip(dimensions, desecurefed_latency, securefed_latency):
        speedup = l2 / l1
        ax.annotate(f'{speedup:.1f}×', xy=(d, l1), xytext=(d*0.6, l1*1.8),
                    fontsize=9, fontweight='bold', color='#4A90A4',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('Model Dimension (log scale)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Encryption Latency (ms, log scale)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.25, linestyle='--', which='both', linewidth=0.8)
    ax.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    plt.savefig('figure_encryption_latency.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('figure_encryption_latency.png', bbox_inches='tight', dpi=300)
    plt.show()
    print("✓ Encryption latency figure generated")
    return fig


def figure_backdoor_resilience():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(attack_scenarios))
    width = 0.2
    
    bars1 = ax.bar(x - 1.5*width, attack_accuracy, width, label='Accuracy', 
                   color='#3498DB', edgecolor='#2C3E50', linewidth=1.2)
    bars2 = ax.bar(x - 0.5*width, attack_precision, width, label='Precision', 
                   color='#27AE60', edgecolor='#2C3E50', linewidth=1.2)
    bars3 = ax.bar(x + 0.5*width, attack_recall, width, label='Recall', 
                   color='#E74C3C', edgecolor='#2C3E50', linewidth=1.2)
    bars4 = ax.bar(x + 1.5*width, attack_f1, width, label='F1 Score', 
                   color='#F39C12', edgecolor='#2C3E50', linewidth=1.2)
    
    for i, bars in enumerate([bars1, bars2, bars3, bars4]):
        for j, bar in enumerate(bars):
            if j == 1:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                        f'{bar.get_height():.2f}', ha='center', va='bottom', 
                        fontweight='bold', fontsize=9)
    
    ax.set_ylabel('Performance Metric (%)', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    ax.set_xticklabels(attack_scenarios, fontsize=11)
    ax.legend(loc='upper left', fontsize=10, frameon=True, fancybox=True, shadow=True, ncol=2)
    ax.grid(True, alpha=0.25, linestyle='--', axis='y', linewidth=0.8)
    
    plt.tight_layout()
    plt.savefig('figure_backdoor_resilience.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('figure_backdoor_resilience.png', bbox_inches='tight', dpi=300)
    plt.show()
    print("✓ Backdoor resilience figure generated")
    return fig


def figure_training_time():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#7FB3D5', '#F4D03F', '#C0392B']
    bars = ax.bar(training_methods, training_times, color=colors, 
                  edgecolor='#2C3E50', linewidth=1.5, width=0.6)
    
    for i, (bar, time_val) in enumerate(zip(bars, training_times)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'{time_val:.1f}s', ha='center', va='bottom', 
                fontweight='bold', fontsize=11)
    
    ax.set_ylabel('Training Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 900)
    ax.grid(True, alpha=0.25, linestyle='--', axis='y', linewidth=0.8)
    
    plt.tight_layout()
    plt.savefig('figure_training_time.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('figure_training_time.png', bbox_inches='tight', dpi=300)
    plt.show()
    print("✓ Training time figure generated")
    return fig


def figure_scalability():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(clients, desecurefed_scalability, 'o-', linewidth=2.5, markersize=10, 
            label='DeSecureFed', color='#4A90A4', markerfacecolor='white', markeredgewidth=2)
    ax.plot(clients, securefed_scalability, 's-', linewidth=2.5, markersize=10, 
            label='SecureFed+', color='#C0392B', markerfacecolor='white', markeredgewidth=2)
    ax.plot(clients, fedavg_scalability, '^-', linewidth=2.5, markersize=10, 
            label='FedAvg', color='#27AE60', markerfacecolor='white', markeredgewidth=2)
    
    for c, d in zip(clients, desecurefed_scalability):
        ax.annotate(f'{d}%', xy=(c, d), xytext=(c-3, d-0.25),
                    fontsize=9, fontweight='bold', color='#4A90A4',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('Number of Clients', fontsize=13, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 110)
    ax.set_ylim(98.5, 100.5)
    ax.set_xticks(clients)
    ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.8)
    ax.legend(loc='lower left', fontsize=11, frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    plt.savefig('figure_scalability.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('figure_scalability.png', bbox_inches='tight', dpi=300)
    plt.show()
    print("✓ Scalability figure generated")
    return fig


def main():
    print("=" * 70)
    print("DESECUREFED FIGURE GENERATION")
    print("=" * 70)
    print("\nGenerating figures from 10M sample results...\n")
    
    figure_accuracy_f1()
    figure_precision_recall()
    figure_encryption_latency()
    figure_backdoor_resilience()
    figure_training_time()
    figure_scalability()
    
    print("\n" + "=" * 70)
    print("ALL FIGURES GENERATED")
    print("=" * 70)


if __name__ == "__main__":
    main()