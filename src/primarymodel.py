# ── IMPORTS ──────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import warnings
import joblib
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    f1_score, classification_report,
    balanced_accuracy_score, make_scorer
)

# ── 1. LOAD DATA ──────────────────────────────────────────────────────────────
DATASET_PATH = "/Users/yuvi/Desktop/VS Code/langchain/models/antibiotic-resistance-predictor/dataset/raw/Dataset.xlsx"   # ← update path as needed

df = pd.read_excel(DATASET_PATH)
df.columns = df.columns.str.strip().str.lower()

ANTIBIOTIC_COLS = ['imipenem', 'ceftazidime', 'gentamicin', 'augmentin', 'ciprofloxacin']

print("=" * 65)
print("ANTIBIOTIC RESISTANCE — PRIMARY MODEL")
print("=" * 65)
print(f"  Samples   : {len(df)}")
print(f"  Locations : {df['location'].nunique()}")
print(f"  Antibiotics: {', '.join(ANTIBIOTIC_COLS)}\n")

# ── 2. CLINICALLY VALID LABELING (CLSI M100 Disk Diffusion Breakpoints) ──────
#
#  Zone diameter (mm) thresholds from CLSI M100 standard.
#  In disk diffusion: LARGER zone → MORE sensitive (antibiotic diffuses further)
#  0 mm = no inhibition = fully resistant
#
CLSI_BREAKPOINTS = {
    'imipenem':      {'S': 16, 'R': 13},   # Carbapenem
    'ceftazidime':   {'S': 18, 'R': 14},   # 3rd-gen Cephalosporin
    'gentamicin':    {'S': 15, 'R': 12},   # Aminoglycoside
    'augmentin':     {'S': 18, 'R': 13},   # Amoxicillin-clavulanate
    'ciprofloxacin': {'S': 21, 'R': 15},   # Fluoroquinolone
}
# Labels: 0 = Sensitive (S), 1 = Intermediate (I), 2 = Resistant (R)

def apply_clsi(val, s_thresh, r_thresh):
    if val >= s_thresh:   return 0
    elif val <= r_thresh: return 2
    else:                 return 1

CLASS_COLS = []
for col in ANTIBIOTIC_COLS:
    bp = CLSI_BREAKPOINTS[col]
    label_col = f'{col}_cls'
    df[label_col] = df[col].apply(lambda x: apply_clsi(x, bp['S'], bp['R']))
    CLASS_COLS.append(label_col)

print("CLASS DISTRIBUTION (0=Sensitive | 1=Intermediate | 2=Resistant)")
print("-" * 55)
for col, lc in zip(ANTIBIOTIC_COLS, CLASS_COLS):
    vc = df[lc].value_counts().sort_index()
    parts = [f"S={vc.get(0,0)}", f"I={vc.get(1,0)}", f"R={vc.get(2,0)}"]
    print(f"  {col.upper():15}: {' | '.join(parts)}")

# ── 3. FEATURE ENGINEERING ───────────────────────────────────────────────────
#
#  Even with only location as metadata, we extract rich signal:
#    - Split location into city × surface type
#    - City-level mean zone size per antibiotic (captures local resistance ecology)
#    - Surface-level mean zone size (T=toilet/sink, C=counter, S=sink/surface)
#    - Aggregate resistance burden (mean/min zone across all antibiotics)
#    - Zero count (number of complete-resistance readings per isolate)
#
df[['city', 'surface']] = df['location'].str.split('-', expand=True)

for col in ANTIBIOTIC_COLS:
    df[f'{col}_city_mean'] = df.groupby('city')[col].transform('mean')
    df[f'{col}_surf_mean'] = df.groupby('surface')[col].transform('mean')

df['mean_zone']  = df[ANTIBIOTIC_COLS].mean(axis=1)    # overall susceptibility proxy
df['min_zone']   = df[ANTIBIOTIC_COLS].min(axis=1)     # worst antibiotic performance
df['zero_count'] = (df[ANTIBIOTIC_COLS] == 0).sum(axis=1)  # count of total resistance

FEATURE_COLS = (
    ['city', 'surface'] +
    [f'{c}_city_mean' for c in ANTIBIOTIC_COLS] +
    [f'{c}_surf_mean' for c in ANTIBIOTIC_COLS] +
    ['mean_zone', 'min_zone', 'zero_count']
)
CAT_FEATURES = ['city', 'surface']
NUM_FEATURES  = [c for c in FEATURE_COLS if c not in CAT_FEATURES]

X = df[FEATURE_COLS]
y = df[CLASS_COLS]

print(f"\nFEATURES: {len(FEATURE_COLS)} total ({len(CAT_FEATURES)} categorical, {len(NUM_FEATURES)} numeric)\n")

# ── 4. PREPROCESSING ─────────────────────────────────────────────────────────
preprocessor = ColumnTransformer(transformers=[
    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CAT_FEATURES),
    ('num', 'passthrough', NUM_FEATURES)
])

# ── 5. MODEL — Random Forest with Balanced Class Weights ────────────────────
#
#  Why Random Forest?
#   - Robust to the small dataset size (n=274)
#   - Handles multi-class targets natively
#   - class_weight='balanced' compensates for imbalanced S/I/R distributions
#   - Feature importances available out-of-box
#
rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_leaf=2,
    max_features='sqrt',
    class_weight='balanced',    # ← key upgrade: handles imbalanced S/I/R
    oob_score=True,
    random_state=42,
    n_jobs=-1
)

model   = MultiOutputClassifier(rf, n_jobs=-1)
pipeline = Pipeline([('pre', preprocessor), ('model', model)])

# ── 6. CROSS-VALIDATION ──────────────────────────────────────────────────────
print("CROSS-VALIDATION (5-fold Stratified)")
print("-" * 55)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_f1     = {col: [] for col in ANTIBIOTIC_COLS}
cv_bal_acc = {col: [] for col in ANTIBIOTIC_COLS}

for fold, (tr_idx, te_idx) in enumerate(skf.split(X, y.iloc[:, 0]), 1):
    X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
    y_tr, y_te = y.iloc[tr_idx], y.iloc[te_idx]
    pipeline.fit(X_tr, y_tr)
    y_pred = pipeline.predict(X_te)
    fold_f1s = []
    for i, col in enumerate(ANTIBIOTIC_COLS):
        f1 = f1_score(y_te.iloc[:, i], y_pred[:, i], average='macro', zero_division=0)
        ba = balanced_accuracy_score(y_te.iloc[:, i], y_pred[:, i])
        cv_f1[col].append(f1)
        cv_bal_acc[col].append(ba)
        fold_f1s.append(f1)
    print(f"  Fold {fold}:  mean macro-F1 = {np.mean(fold_f1s):.4f}")

print("\nCV RESULTS:")
print(f"{'Antibiotic':17} {'F1-Macro':>12} {'Bal-Accuracy':>13}")
print("-" * 45)
all_f1 = []
for col in ANTIBIOTIC_COLS:
    mf = np.mean(cv_f1[col])
    ma = np.mean(cv_bal_acc[col])
    all_f1.append(mf)
    print(f"  {col.upper():15} {mf:>12.4f} {ma:>13.4f}")
print(f"\n  ★ OVERALL CV F1 : {np.mean(all_f1):.4f}")

# ── 7. FINAL MODEL — train on ALL data ───────────────────────────────────────
print("\nTraining final model on full dataset...")
pipeline.fit(X, y)
y_pred_full = pipeline.predict(X)
print("✅ Done.\n")

# ── 8. CLASSIFICATION REPORTS ────────────────────────────────────────────────
f1_results = {}
print("=" * 65)
print("CLASSIFICATION REPORTS")
print("=" * 65)
for i, col in enumerate(ANTIBIOTIC_COLS):
    print(f"\n--- {col.upper()} ---")
    print(classification_report(
        y.iloc[:, i], y_pred_full[:, i],
        target_names=['Sensitive', 'Intermediate', 'Resistant'],
        zero_division=0
    ))
    f1_results[col] = f1_score(y.iloc[:, i], y_pred_full[:, i],
                                average='macro', zero_division=0)

# ── 9. FEATURE IMPORTANCE ────────────────────────────────────────────────────
print("=" * 65)
print("FEATURE IMPORTANCE (RF Gini impurity, top 5 per antibiotic)")
print("=" * 65)
ohe_names = (pipeline.named_steps['pre']
             .named_transformers_['cat']
             .get_feature_names_out(['city', 'surface'])
             .tolist())
all_feat_names = ohe_names + NUM_FEATURES

importance_records = []
for i, col in enumerate(ANTIBIOTIC_COLS):
    imp = pipeline.named_steps['model'].estimators_[i].feature_importances_
    top5 = np.argsort(imp)[::-1][:5]
    print(f"\n  {col.upper()}")
    for rank, idx in enumerate(top5, 1):
        fname = all_feat_names[idx] if idx < len(all_feat_names) else f"feat_{idx}"
        print(f"    {rank}. {fname:35} {imp[idx]:.4f}")
        importance_records.append({'antibiotic': col, 'feature': fname, 'importance': imp[idx]})

importance_df = pd.DataFrame(importance_records)

# ── 10. MDR & RESISTANCE PROFILING ───────────────────────────────────────────
df['n_resistant'] = sum((df[lc] == 2) for lc in CLASS_COLS)
df['is_MDR']      = df['n_resistant'] >= 3

resist_df = pd.DataFrame({
    col: df.groupby('location')[lc].apply(lambda x: round((x == 2).mean() * 100, 1))
    for col, lc in zip(ANTIBIOTIC_COLS, CLASS_COLS)
})

print("\n\n" + "=" * 65)
print("RESISTANCE PROFILING")
print("=" * 65)
print("\nResistance Prevalence (%) by Location:")
print(resist_df.to_string())

city_mdr = df.groupby('city')['is_MDR'].mean() * 100
print(f"\nOverall MDR Rate (≥3 resistant): {df['is_MDR'].mean()*100:.1f}%")
print("\nMDR Rate by City:")
for city, rate in city_mdr.items():
    bar = '█' * int(rate / 5)
    print(f"  {city}: {rate:5.1f}%  {bar}")

# ── 11. TREATMENT RECOMMENDATIONS ────────────────────────────────────────────
TREATMENT = {
    'imipenem':      {
        'class': 'Carbapenem (last resort)',
        'sensitive': 'Suitable for severe/refractory infections — reserve for carbapenem-appropriate cases',
        'resistant': '⚠️  CRITICAL: Carbapenem resistance → test Polymyxin B, Colistin, Ceftazidime-avibactam'
    },
    'ceftazidime':   {
        'class': '3rd-gen Cephalosporin',
        'sensitive': 'Appropriate empiric therapy for Pseudomonas/Enterobacteriaceae',
        'resistant': '⚠️  Likely ESBL producer → use Carbapenems or Piperacillin-tazobactam'
    },
    'gentamicin':    {
        'class': 'Aminoglycoside',
        'sensitive': 'Effective in synergistic combinations (e.g., with β-lactams)',
        'resistant': '⚠️  Aminoglycoside resistance → test Amikacin, Tobramycin (may retain activity)'
    },
    'augmentin':     {
        'class': 'Penicillin + β-lactamase inhibitor',
        'sensitive': 'Good for community-acquired infections and mild-moderate severity',
        'resistant': '⚠️  Extended resistance → Penicillinase-producing strain; escalate to cephalosporins'
    },
    'ciprofloxacin': {
        'class': 'Fluoroquinolone',
        'sensitive': 'Broad-spectrum; suitable for UTIs, respiratory, GI infections',
        'resistant': '⚠️  Fluoroquinolone resistance (QRDR mutation likely) → avoid empiric use'
    }
}

print("\n\n" + "=" * 65)
print("TREATMENT STRATEGY RECOMMENDATIONS")
print("=" * 65)
for col in ANTIBIOTIC_COLS:
    resist_pct = (df[f'{col}_cls'] == 2).mean() * 100
    rec = TREATMENT[col]
    print(f"\n{col.upper()} [{rec['class']}] — Resistance: {resist_pct:.1f}%")
    if resist_pct > 50:
        print(f"  HIGH RESISTANCE: {rec['resistant']}")
    elif resist_pct > 20:
        print(f"  MODERATE RESISTANCE: Consider susceptibility testing before prescribing")
        print(f"  Sensitive guidance: {rec['sensitive']}")
    else:
        print(f"  LOW RESISTANCE: {rec['sensitive']}")

# ── 12. SAVE ARTIFACTS ───────────────────────────────────────────────────────
joblib.dump(pipeline,     'primarymodel.pkl')
joblib.dump(FEATURE_COLS, 'feature_cols.pkl')
importance_df.to_csv('feature_importance.csv', index=False)
resist_df.to_csv('resistance_by_location.csv')
df[['location','city','surface','is_MDR','n_resistant'] + CLASS_COLS]\
    .to_csv('labeled_dataset.csv', index=False)

print("\n\n" + "=" * 65)
print("FINAL F1 SCORES SUMMARY")
print("=" * 65)
for k, v in f1_results.items():
    stars = '★' * min(5, int(v * 5))
    print(f"  {k.upper():17}: {v:.4f}  {stars}")
print(f"\n  ★ OVERALL MACRO F1 : {np.mean(list(f1_results.values())):.4f}")
print("\n✅ Artifacts saved: primarymodel.pkl, feature_importance.csv,")
print("   resistance_by_location.csv, labeled_dataset.csv")
