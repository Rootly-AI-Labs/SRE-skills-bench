import matplotlib.pyplot as plt
import csv
from adjustText import adjust_text

# Read and parse the data from data.csv
def parse_data(filename):
    models = []
    costs = []
    rootly_gmcq = []
    azure_k8s_mcq = []
    s3_security_mcq = []

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            if not row.get('model'):
                continue

            model = row['model'].strip()

            # Extract cost as float (remove $ and convert)
            cost_str = row['output token cost per million tokens'].replace('$', '').strip()
            try:
                cost = float(cost_str)
            except ValueError:
                continue

            # Extract accuracy percentages
            try:
                rootly = float(row['rootly gmcq'].replace('%', '').strip()) if row['rootly gmcq'].strip() else None
                azure = float(row['azure-k8s-mcq'].replace('%', '').strip()) if row['azure-k8s-mcq'].strip() else None
                s3 = float(row['s3-security-mcq'].replace('%', '').strip()) if row['s3-security-mcq'].strip() else None

                models.append(model)
                costs.append(cost)
                rootly_gmcq.append(rootly)
                azure_k8s_mcq.append(azure)
                s3_security_mcq.append(s3)
            except (ValueError, KeyError):
                continue

    return models, costs, rootly_gmcq, azure_k8s_mcq, s3_security_mcq

# Parse the data
models, costs, rootly_gmcq, azure_k8s_mcq, s3_security_mcq = parse_data('static/data.csv')

# Create three scatter plots
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Plot 1: Rootly GMCQ
ax1 = axes[0]
ax1.set_ylim(74, 101)
ax1.set_xlim(-1, 16.5)
ax1.set_xlabel('Output Token Cost per Million ($)', fontsize=11)
ax1.set_ylabel('Accuracy (%)', fontsize=11)
ax1.set_title('Rootly GMCQ', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)

valid_data = [(c, r, m) for c, r, m in zip(costs, rootly_gmcq, models) if r is not None]
texts1 = []
if valid_data:
    x1, y1, labels1 = zip(*valid_data)
    ax1.scatter(x1, y1, s=25, alpha=0.6, color='#351c75')
    for i, label in enumerate(labels1):
        text = ax1.annotate(label, (x1[i], y1[i]), fontsize=7, ha='center', va='center', alpha=0.85)
        texts1.append(text)

if texts1:
    adjust_text(texts1, ax=ax1)

# Plot 2: Azure K8s MCQ
ax2 = axes[1]
ax2.set_ylim(38, 102)
ax2.set_xlim(-1, 16.5)
ax2.set_xlabel('Output Token Cost per Million ($)', fontsize=11)
ax2.set_ylabel('Accuracy (%)', fontsize=11)
ax2.set_title('Azure K8s MCQ', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)

valid_data = [(c, a, m) for c, a, m in zip(costs, azure_k8s_mcq, models) if a is not None]
texts2 = []
if valid_data:
    x2, y2, labels2 = zip(*valid_data)
    ax2.scatter(x2, y2, s=25, alpha=0.6, color='#351c75')
    for i, label in enumerate(labels2):
        text = ax2.annotate(label, (x2[i], y2[i]), fontsize=7, ha='center', va='center', alpha=0.85)
        texts2.append(text)

if texts2:
    adjust_text(texts2, ax=ax2)

# Plot 3: S3 Security MCQ
ax3 = axes[2]
ax3.set_ylim(28, 102)
ax3.set_xlim(-1, 16.5)
ax3.set_xlabel('Output Token Cost per Million ($)', fontsize=11)
ax3.set_ylabel('Accuracy (%)', fontsize=11)
ax3.set_title('S3 Security MCQ', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)

valid_data = [(c, s, m) for c, s, m in zip(costs, s3_security_mcq, models) if s is not None]
texts3 = []
if valid_data:
    x3, y3, labels3 = zip(*valid_data)
    ax3.scatter(x3, y3, s=25, alpha=0.6, color='#351c75')
    for i, label in enumerate(labels3):
        text = ax3.annotate(label, (x3[i], y3[i]), fontsize=7, ha='center', va='center', alpha=0.85)
        texts3.append(text)

if texts3:
    adjust_text(texts3, ax=ax3)

plt.tight_layout(pad=3.0)
plt.subplots_adjust(left=0.06, right=0.98, bottom=0.1, top=0.93, wspace=0.25)
plt.savefig('benchmark_scatter_plots.png', dpi=300)
print("Scatter plots saved to 'benchmark_scatter_plots.png'")
plt.show()
