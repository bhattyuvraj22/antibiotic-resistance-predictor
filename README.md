# 🧬 Antibiotic Resistance Decision Support System

![Banner](https://via.placeholder.com/1200x300/1a4d2a/ffffff?text=Antibiotic+Resistance+Decision+Support)

An AI‑powered tool that predicts antibiotic resistance from **clinical patient data** (species, demographics, risk factors) and **environmental sampling data** (location, surface type). Built with XGBoost and Gradio, this dashboard helps clinicians and researchers make informed decisions by ranking effective antibiotics and visualising co‑resistance patterns.

---

## 📖 Table of Contents
- [Overview](#overview)
- [Datasets](#datasets)
- [Features](#features)
- [Methodology](#methodology)
- [Installation & Setup](#installation--setup)
- [How to Run](#how-to-run)
- [Dashboard Walkthrough](#dashboard-walkthrough)
- [Results](#results)
- [Future Work](#future-work)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## 🔬 Overview
Antimicrobial resistance (AMR) is a global health crisis. This project tackles AMR by providing two complementary prediction models:

- **Clinical Model** – Predicts resistance for 15 antibiotics using patient data (age, gender, diabetes, hypertension, prior hospitalisation, infection frequency) and bacterial species.
- **Environmental Model** – Predicts resistance for 5 antibiotics using location (city) and sampling surface (butcher table, concrete slab, soil) – based on environmental isolates from Nigeria.

The tool outputs the probability of resistance for each antibiotic, suggests the most effective alternatives, and displays feature importance and co‑resistance networks.

---

## 📊 Datasets

### Secondary Dataset (Clinical)
- **Source:** Synthetic clinical dataset (~10,000 isolates)
- **Features:** `Souches` (bacterial species), `Age`, `Gender`, `Diabetes`, `Hypertension`, `Hospital_before`, `Infection_Freq`
- **Targets:** 15 antibiotics (R/S)
- **Cleaned:** Missing values imputed, categorical encodings standardised.

### Primary Dataset (Environmental)
- **Source:** `Dataset.xlsx` – zone diameters for 5 antibiotics, collected from four locations in Nigeria.
- **Features:** `city` (Ede, Ife, Iwo, Osu), `surface_code` (T, C, S)
- **Targets:** 5 antibiotics, classified into **Sensitive / Intermediate / Resistant** based on zone diameter thresholds.
- **Pre‑trained model:** provided as `model.pkl`.

---

## ✨ Features

- **Clinical Prediction Tab**  
  - Input patient demographics and select an antibiotic of interest.  
  - Output: resistance probability, top‑5 recommended antibiotics, probability bar chart, and feature importance plot.

- **Environmental Prediction Tab**  
  - Input city and surface type, select an antibiotic.  
  - Output: resistance class, confidence, probability distribution, and feature importance.

- **Model Performance Tab**  
  - Data table and bar chart of weighted F1 scores for both clinical and environmental models.

- **Co‑resistance Network** (included in the code, but not displayed in the current UI – can be added back if desired)

---

## ⚙️ Methodology

### Data Preprocessing
- **Clinical dataset:**  
  - Split `age/gender` into separate columns.  
  - Standardised binary columns (`Diabetes`, `Hypertension`, `Hospital_before`) to 0/1.  
  - Mapped `Infection_Freq` to numeric (0‑3).  
  - Cleaned species names (e.g., `E.coi` → `Escherichia coli`).  
  - Antibiotic labels: `R` → 1, `S` → 0, other → NaN.  
  - Imputed missing values (median for `Age`, 0 for `Infection_Freq`, 'Unknown' for categoricals).

- **Environmental dataset:**  
  - Zone diameters transformed into three‑class outcomes (Sensitive, Intermediate, Resistant) based on quantiles.  
  - Pre‑trained model uses one‑hot encoding for city and surface.

### Model Training
- **Algorithm:** XGBoost (binary classification)
- **Pipeline:** One‑hot encoding of categorical features, standard scaling of numeric features.
- **Class imbalance:** `scale_pos_weight` adjusted per antibiotic based on training set class ratio.
- **Evaluation:** Weighted F1‑score and ROC‑AUC.

### Performance
- **Clinical models:** F1 scores range from 0.60 to 0.75 across 15 antibiotics.
- **Environmental models:** F1 scores around 0.62–0.73 for the 5 antibiotics.

---

## 💻 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/antibiotic-resistance-dss.git
   cd antibiotic-resistance-dss



   #scrappp
   # 🧬 ResistAI — Antibiotic Resistance Decision Support

A clinical + environmental antibiotic resistance prediction dashboard powered by two ML models (Random Forest + HGB ensemble) and a Flask REST API.

> **For research use only. Not for clinical decision-making without appropriate validation.**

---

## 📁 Project Structure

```
resistai/
├── app.py                    ← Flask API server (entry point)
├── requirements.txt          ← Python dependencies
├── .gitignore
├── README.md
│
├── models/                   ← Place your .pkl files here (not committed to git)
│   ├── model.pkl                      ← Environmental model (Model 1)
│   └── antibiotic_resistance_model_v2.pkl  ← Clinical model (Model 2)
│
├── templates/
│   └── index.html            ← Main dashboard HTML (Jinja2 template)
│
└── static/
    ├── css/
    │   └── main.css          ← All dashboard styles
    └── js/
        └── main.js           ← Chart rendering + fetch() API calls
```

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/your-username/resistai.git
cd resistai
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your model files
Place both `.pkl` files in the `models/` directory:
```
models/
  model.pkl
  antibiotic_resistance_model_v2.pkl
```

> If the models are absent, the app runs in **demo mode** — it still works but returns randomised fallback predictions.

### 5. Run the server
```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## 🔌 API Reference

### Health check
```
GET /health
```
Returns model load status.

### Clinical prediction
```
POST /predict/clinical
Content-Type: application/json

{
  "species":      "Escherichia coli",
  "age":          45,
  "gender":       "M",
  "diabetes":     "No",
  "hypertension": "No",
  "hospital":     "No",
  "inf_freq":     "Rarely",
  "antibiotic":   "CIP"
}
```

Response:
```json
{
  "antibiotic":      "CIP",
  "resistance_prob": 0.62,
  "susceptibility":  0.38,
  "classification":  "Resistant",
  "all_probs":       { "AMX/AMP": 0.45, "CIP": 0.62, ... },
  "recommendations": [{ "name": "GEN", "resistance_prob": 0.18 }, ...],
  "alternatives":    [{ "name": "GEN", "resistance_prob": 0.18 }, ...]
}
```

### Environmental prediction
```
POST /predict/environmental
Content-Type: application/json

{
  "city":          "Ife",
  "surface":       "T",
  "antibiotic":    "ciprofloxacin",
  "sample_source": "Community",
  "species":       "— Any —"
}
```

Response:
```json
{
  "antibiotic":    "ciprofloxacin",
  "city":          "Ife",
  "surface":       "T",
  "probabilities": { "Sensitive": 0.45, "Intermediate": 0.25, "Resistant": 0.30 },
  "prediction":    "Sensitive",
  "confidence":    0.45
}
```

---

## 🌐 Production Deployment

### Using Gunicorn (recommended for Linux servers)
```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### Environment variables
| Variable       | Default | Description                        |
|----------------|---------|------------------------------------|
| `PORT`         | `5000`  | Port to bind the server            |
| `FLASK_DEBUG`  | `false` | Enable debug mode (dev only)       |

---

## 🤖 Models

| Model | File | Description |
|-------|------|-------------|
| Environmental (Model 1) | `models/model.pkl` | Random Forest trained on Nigerian environmental surface swab data. Predicts S/I/R class for 5 antibiotics. |
| Clinical (Model 2) | `models/antibiotic_resistance_model_v2.pkl` | RF + HistGradientBoosting Voting Ensemble. Predicts resistance probability for 15 antibiotics from patient demographics and clinical features. |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.3 | Web server + API routing |
| flask-cors | 4.0.1 | Cross-origin resource sharing |
| joblib | 1.4.2 | Model serialisation |
| scikit-learn | 1.5.1 | ML pipeline + prediction |
| numpy | 1.26.4 | Numerical operations |
| pandas | 2.2.2 | Dataframe construction for model input |
| gunicorn | 22.0.0 | Production WSGI server |

---

## 📜 License

This project is for academic research purposes only. The predictive models were trained on a Nigerian clinical and environmental dataset. Results should not be used for direct clinical decision-making.