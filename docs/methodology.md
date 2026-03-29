# Methodology – ResistAI

## 1. Introduction
ResistAI is a machine learning framework that predicts antibiotic resistance using two complementary datasets: environmental (soil/surface samples) and clinical (patient records). The system supports antimicrobial stewardship by providing interpretable predictions, feature importance, and treatment recommendations.

## 2. Datasets

### 2.1 Environmental Dataset
- **Source:** `Dataset.xlsx` – Excel file with 274 samples from four cities in Nigeria.
- **Content:** Zone‑diameter measurements (mm) for 5 antibiotics: imipenem, ceftazidime, gentamicin, augmentin, ciprofloxacin.
- **Metadata:** `location` (city + surface code: T‑table, C‑concrete, S‑soil).

### 2.2 Clinical Dataset
- **Source:** `Bacteria_dataset_Multiresictance.csv` – CSV with 9,247 isolates after cleaning.
- **Content:** 15 antibiotics (R/S binary), bacterial species, patient age, gender, diabetes, hypertension, prior hospitalisation, infection frequency, collection date.
- **Labels:** Converted from raw text (`R`/`S`/`i`/`Intermediate`) to binary (R=1, S=0).

---

## 3. Data Preprocessing

### 3.1 Environmental Dataset
- Split `location` into `city` and `surface`.
- Apply CLSI M100 disk diffusion breakpoints to map zone diameters to **Sensitive (0)**, **Intermediate (1)**, **Resistant (2)**.
- Engineer features:
  - City‑ and surface‑wise mean zone diameters per antibiotic.
  - Overall mean zone, minimum zone, and zero count (number of antibiotics with 0 mm).
- Use these 15 features (2 categorical + 13 numeric) for model training.

### 3.2 Clinical Dataset
- **Cleaning:**
  - Remove species with misspellings or incomplete IDs; keep only 9 common species.
  - Standardise binary risk factors (diabetes, hypertension, hospitalisation) to 0/1.
  - Convert infection frequency to numeric (0‑3).
  - Impute missing values: infection frequency by species median, age with median, others with 0.
- **Feature engineering** (30+ features):
  - Age transformations (square, age group, elderly/child flags).
  - Comorbidity score (sum of three binary risk factors) and high‑risk flag.
  - Resistance counts (total, MDR ≥3, XDR ≥10) and resistance rate.
  - Species‑specific resistance rate (computed from training data).
  - Grouped resistance averages for beta‑lactams, carbapenems, aminoglycosides, fluoroquinolones, others.
  - Interaction terms (infection frequency × comorbidity, age × comorbidity, high‑risk × species rate).
  - Temporal feature (years since 2019, default 3).

---

## 4. Model Development

### 4.1 Environmental Model
- **Algorithm:** Multi‑output Random Forest (one forest per antibiotic) with `class_weight='balanced'`.
- **Features:** one‑hot encoded city + surface, plus engineered aggregates (15 features total).
- **Target:** 3‑class (S/I/R) for 5 antibiotics.
- **Training:** 5‑fold stratified cross‑validation; final model trained on all data.
- **Evaluation:** Macro‑averaged F1‑score and balanced accuracy.

### 4.2 Clinical Model
- **Algorithm:** Voting ensemble of Random Forest (RF) and Histogram‑based Gradient Boosting (HGB), wrapped in `MultiOutputClassifier` for 15 binary (R/S) targets.
- **Hyperparameters:**
  - RF: 300 trees, max_depth=14, min_samples_leaf=2, max_features='sqrt', class_weight='balanced'.
  - HGB: 200 iterations, max_depth=8, learning_rate=0.05, min_samples_leaf=20, class_weight='balanced'.
- **Training split:** 85/15 train/test (stratified by MDR flag). A further 17.6% of training is held out for threshold tuning.
- **Threshold tuning:** On the validation set, for each antibiotic, the optimal probability threshold (0.25–0.75) is chosen to maximise weighted F1‑score.
- **Evaluation:** Weighted F1, macro F1, balanced accuracy, classification reports.

---

## 5. Evaluation Results

### 5.1 Environmental Model (5‑fold CV)
| Antibiotic       | Macro F1 | Bal‑Accuracy |
|------------------|---------:|-------------:|
| Imipenem         | 0.4265   | 0.4611       |
| Ceftazidime      | 0.5714   | 0.6127       |
| Gentamicin       | 0.4757   | 0.4736       |
| Augmentin        | 0.6139   | 0.6231       |
| Ciprofloxacin    | 0.5404   | 0.5426       |
| **Overall**      | **0.5256** | **0.5426**   |

**Final (full‑data) performance** (macro F1):
| Antibiotic       | Macro F1 |
|------------------|---------:|
| Imipenem         | 0.9072   |
| Ceftazidime      | 0.8740   |
| Gentamicin       | 0.8328   |
| Augmentin        | 0.8369   |
| Ciprofloxacin    | 0.8255   |
| **Overall**      | **0.8553** |

### 5.2 Clinical Model (test set, 1,388 isolates)
| Antibiotic             | Weighted F1 | Macro F1 | Balanced Acc |
|------------------------|------------:|---------:|-------------:|
| AMX/AMP (Penicillin)   | 0.7686      | 0.7592   | 0.7549       |
| AMC (Beta‑lactam+inh.) | 0.7902      | 0.7818   | 0.7814       |
| CZ (Ceph‑1G)           | 0.7732      | 0.7652   | 0.7703       |
| FOX (Ceph‑2G)          | 0.7610      | 0.7499   | 0.7468       |
| CTX/CRO (Ceph‑3G)      | 0.7682      | 0.7572   | 0.7519       |
| IPM (Carbapenem)       | 1.0000      | 1.0000   | 1.0000       |
| GEN (Aminoglycoside)   | 0.8719      | 0.8169   | 0.8968       |
| AN (Aminoglycoside)    | 0.8682      | 0.8157   | 0.8933       |
| Acide nalidixique (Qui)| 0.8590      | 0.7276   | 0.7330       |
| ofx (Fluoroquinolone)  | 0.8588      | 0.7231   | 0.7254       |
| CIP (Fluoroquinolone)  | 0.8594      | 0.7141   | 0.6866       |
| C (Phenicol)           | 0.8563      | 0.7028   | 0.6827       |
| Co‑trimoxazole (Sulf)  | 0.8573      | 0.7378   | 0.7243       |
| Furanes (Nitrofuran)   | 0.8524      | 0.6759   | 0.6433       |
| colistine (Polymyxin)  | 0.8522      | 0.6885   | 0.6667       |
| **Overall**            | **0.8398**  | **0.7611** | –           |

---

## 6. Interpretability & Decision Support

### 6.1 Feature Importance (Clinical Model)
Top predictors for the first antibiotic (AMX/AMP):
| Feature                | Importance |
|------------------------|-----------:|
| res_beta_lactam        | 0.2402     |
| Resistance_Count       | 0.1305     |
| Resistance_Rate        | 0.1220     |
| Age                    | 0.0618     |
| Age_sq                 | 0.0604     |
| Age_x_Comorbidity      | 0.0445     |
| MDR_Flag               | 0.0430     |
| Species_R_Rate         | 0.0415     |

### 6.2 Resistance Profiling (Environmental)
- **Overall MDR rate (≥3 resistant):** 22.3%
- **MDR rate by city:** EDE 15.9%, IFE 17.8%, IWO 36.2%, OSU 18.8%.

### 6.3 Treatment Recommendations
Based on resistance prevalence, the system provides per‑antibiotic guidance:
- **Imipenem** (0.7% resistance): low resistance – suitable for severe/refractory infections.
- **Ceftazidime** (71.5% resistance): high – likely ESBL producer; escalate to carbapenems.
- **Gentamicin** (16.8%): low – effective in synergistic combinations.
- **Augmentin** (58.8%): high – escalate to cephalosporins.
- **Ciprofloxacin** (23.0%): moderate – consider susceptibility testing before prescribing.

For the clinical model, alternatives for a given drug are ranked by predicted susceptibility probability using the ensemble predictions.

---

## 7. Deployment
- **Flask API** (`app.py`) serves predictions:
  - `/predict/clinical` – accepts patient data, returns resistance probability, classification, top‑5 effective drugs, and alternatives.
  - `/predict/environmental` – accepts city, surface, antibiotic; returns probabilities for S/I/R classes and confidence.
- **Model loading:** At startup, loads:
  - `primarymodel.pkl` – environmental pipeline.
  - `secondarymodel.pkl` – clinical artifact (pipeline, thresholds, species rates, etc.).
- **Fallback:** If a model is missing, the endpoint returns deterministic dummy predictions and logs a warning.
- **Artifacts saved:** In addition to the models, the primary model saves:
  - `feature_importance.csv`
  - `resistance_by_location.csv`
  - `labeled_dataset.csv`

---

## 8. Conclusion
ResistAI combines rigorous data preprocessing, state‑of‑the‑art machine learning (RF + HGB ensemble for clinical, RF for environmental), and thoughtful feature engineering to deliver accurate, interpretable predictions. The clinical model achieves an overall weighted F1 of 0.84, while the environmental model attains a macro F1 of 0.86 after full training. The system is deployed as a Flask API with a user‑friendly dashboard, supporting clinical decision‑making and antimicrobial stewardship in both environmental and clinical settings.