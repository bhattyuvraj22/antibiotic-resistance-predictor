<div align="center">

# 🧬 ResistAI

### Antibiotic Resistance Decision Support System

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Visit%20App-00ff9d?style=for-the-badge&labelColor=060b12)](https://antibiotic-resistance-predictor-fga9.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Chart.js](https://img.shields.io/badge/Chart.js-Dashboard-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org)
[![AMR](https://img.shields.io/badge/Mission-Fight%20AMR-00ff9d?style=for-the-badge&labelColor=060b12)](https://github.com/bhattyuvraj22/antibiotic-resistance-predictor)

<br/>

> 🏆 **Predicting antibiotic resistance before culture results arrive —**
> combining clinical patient data and environmental sampling intelligence
> into one real-time AI dashboard.

<br/>

### 🌐 [https://antibiotic-resistance-predictor-fga9.onrender.com](https://antibiotic-resistance-predictor-fga9.onrender.com/)

> 🚨 **Note:** Backend is hosted on free tier (Render), so the first request may take **~20–30 seconds** due to cold start. Click the button below to wake the server before demoing.

<br/>

[![Wake Server](https://img.shields.io/badge/⚡%20Wake%20Server-Click%20Before%20Demo-f5a623?style=for-the-badge&labelColor=1a2d42)](https://antibiotic-resistance-predictor-fga9.onrender.com/health)

<br/>

![Overview Dashboard](docs/Screenshots/01-overview-dashboard.png)

</div>

---

## 🌍 The Problem We're Solving

**Antimicrobial resistance (AMR) kills 1.27 million people every year** and is on track to become the world's leading cause of death by 2050. A core challenge: clinicians must prescribe antibiotics *before* lab culture results are back — often 48–72 hours too late.

**ResistAI** bridges that gap. It uses machine learning trained on real clinical and environmental data to predict, in seconds, which antibiotics a bacterial strain is likely resistant to — and which ones will still work.

---

## ✨ What ResistAI Does

| Capability | Details |
|-----------|---------|
| 🏥 **Clinical Prediction** | Input patient demographics + bacterial species → instant resistance probability for **15 antibiotics** |
| 🌿 **Environmental Prediction** | Input city + surface type → resistance class for **5 antibiotics** from Nigerian environmental isolates |
| 💊 **Treatment Ranking** | Ranks antibiotics by predicted efficacy — recommends the best options first |
| 🧬 **Gene & Feature Insight** | Shows which resistance genes and patient factors drive predictions |
| 📈 **Model Performance** | Full F1 scores, ROC curves, confusion matrix — transparent and auditable |
| 🎯 **Stewardship Principles** | Evidence-based antibiotic stewardship rules built into the UI |
| 🔄 **Smart Fallback** | If backend is unavailable, the UI still runs with intelligent client-side fallback predictions |

---

## 🖥️ UI Preview

| Page | Preview |
|------|---------|
| 📊 **Overview Dashboard** | ![Overview](docs/Screenshots/01-overview-dashboard.png) |
| 🔬 **Clinical Prediction** | ![Clinical](docs/Screenshots/03-clinical-prediction.png) |
| 🌿 **Environmental Prediction** | ![Environmental](docs/Screenshots/04-environmental-prediction.png) |
| 🧬 **Gene & Features** | ![Genes](docs/Screenshots/05-gene-features.png) |
| 📈 **Model Performance** | ![Performance](docs/Screenshots/06-model-performance-metrics.png) |
| 💊 **Treatment Strategy** | ![Strategy](docs/Screenshots/08-treatment-strategy.png) |

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/bhattyuvraj22/antibiotic-resistance-predictor.git
cd antibiotic-resistance-predictor

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### ⚠️ Model File Setup — Required Before Running

The clinical model (`secondarymodel.pkl`) is **not included in this repository** due to its file size. You have two options to set it up:

---

**Option A — Download the pre-trained model (recommended)**

Download `secondarymodel.pkl` from Google Drive and place it in the `models/` directory:

```
📥 Download: https://drive.google.com/file/d/142NDXb9ravI0O-zrJH2Xw5FaJQILb6i1/view?usp=drive_link
📁 Save to:  models/secondarymodel.pkl
```

---

**Option B — Retrain the model locally**

If you prefer to train the model from scratch using the bundled dataset:

```bash
python src/secondarymodel.py
```

> ⏱️ **Note:** Training may take several minutes depending on your hardware. Once complete, `secondarymodel.pkl` will be saved automatically to the `models/` directory.

---

```bash
# 4. Run the server
python src/app.py
```

Open **http://localhost:5500** in your browser. 🎉

---

## 📁 Project Structure

```
antibiotic-resistance-predictor/
│
├── 📂 Interface/               ← Frontend (HTML, CSS, JS)
│   ├── index.html
│   ├── main.css
│   └── main.js
│
├── 📂 dataset/
│   ├── clean/                  ← Processed datasets
│   └── raw/
│       ├── Bacteria_dataset_Multiresic...
│       └── Dataset.xlsx        ← Environmental sampling data (Nigeria)
│
├── 📂 docs/
│   ├── methodology.md
│   └── Screenshots/            ← App preview images
│
├── 📂 models/                  ← Trained ML model artifacts
│   ├── primarymodel.pkl        ← Environmental model
│   ├── secondarymodel.pkl      ← Clinical model (ensemble) ⚠️ Not in repo — see setup above
│   └── feature_cols.pkl
│
├── 📂 src/                     ← Flask backend
│   ├── app.py                  ← Main API server ⭐
│   ├── primarymodel.py         ← Environmental model training
│   └── secondarymodel.py       ← Clinical model training
│
├── .python-version             ← Pins Python 3.13 for Render
├── requirements.txt
└── README.md
```

---

## 🤖 ML Models

### 🟢 Primary Model — Environmental
| Property | Details |
|----------|---------|
| **File** | `models/primarymodel.pkl` |
| **Data** | Nigerian surface swab data (soil, concrete, butcher tables) |
| **Input** | City (Ede, Ife, Iwo, Osu) + Surface Type |
| **Output** | Sensitive / Intermediate / Resistant for 5 antibiotics |
| **Algorithm** | Random Forest MultiOutputClassifier |
| **F1 Score** | 0.62 – 0.73 across antibiotics |

### 🔵 Secondary Model — Clinical
| Property | Details |
|----------|---------|
| **File** | `models/secondarymodel.pkl` |
| **Availability** | ⚠️ Not included in repo — [download from Google Drive](https://drive.google.com/file/d/142NDXb9ravI0O-zrJH2Xw5FaJQILb6i1/view?usp=drive_link) or regenerate via `python src/secondarymodel.py` |
| **Data** | Clinical dataset (~10,000 isolates) |
| **Input** | Species, Age, Gender, Diabetes, Hypertension, Hospital history, Infection frequency |
| **Output** | Resistance probability for **15 antibiotics** |
| **Algorithm** | VotingClassifier (HistGradientBoosting + Random Forest) |
| **F1 Score** | 0.62 – 0.75 across antibiotics |
| **ROC AUC** | **0.91** (Gentamicin model) |

---

## 📈 Model Performance

```
Clinical Model — 15 antibiotics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Avg. Accuracy     87%
  Best ROC AUC      0.91  (Gentamicin)
  F1 Range          0.62 – 0.75
  Resistance Rate   38% across isolates

Environmental Model — 5 antibiotics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  F1 Range          0.62 – 0.73
  Classes           Sensitive / Intermediate / Resistant
```

---

## 🔌 API Reference

### `GET /health`
```json
{ "status": "ok", "models": { "clinical": true, "environmental": true } }
```

### `POST /predict/clinical`
```json
// Request
{
  "species": "Escherichia coli", "age": 45, "gender": "M",
  "diabetes": "No", "hypertension": "No", "hospital": "Yes",
  "inf_freq": "Often", "antibiotic": "CIP"
}
// Response
{
  "antibiotic": "CIP", "resistance_prob": 0.62, "susceptibility": 0.38,
  "classification": "Resistant",
  "recommendations": [{ "name": "GEN", "resistance_prob": 0.18 }],
  "alternatives":    [{ "name": "IPM", "resistance_prob": 0.22 }]
}
```

### `POST /predict/environmental`
```json
// Request
{ "city": "Ife", "surface": "T", "antibiotic": "ciprofloxacin" }
// Response
{
  "prediction": "Sensitive", "confidence": 0.45,
  "probabilities": { "Sensitive": 0.45, "Intermediate": 0.25, "Resistant": 0.30 }
}
```

---

## 📊 Antibiotics Covered

| Clinical (15) | Environmental (5) |
|--------------|------------------|
| AMX/AMP, AMC, CZ, FOX, CTX/CRO | Imipenem |
| IPM, GEN, AN, ofx, CIP | Ceftazidime |
| Acide nalidixique, C | Gentamicin |
| Co-trimoxazole, Furanes, colistine | Augmentin, Ciprofloxacin |

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, Flask 3.0, Flask-CORS |
| **ML** | scikit-learn, joblib, NumPy, pandas |
| **Frontend** | Vanilla JS, Chart.js, CSS3 |
| **Hosting** | Render (free tier) |

---

## 🌐 Deployment

```bash
# Gunicorn (production)
gunicorn -w 2 -b 0.0.0.0:5500 src.app:app
```

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5500` | Server port |
| `FLASK_DEBUG` | `false` | Debug mode |

---

## 🙏 Acknowledgements

- Environmental dataset from Nigerian surface sampling studies (Ede, Ife, Iwo, Osu)
- Built with scikit-learn, Flask, and Chart.js
- Motivated by the WHO global action plan on antimicrobial resistance

---

<div align="center">

**Built to fight one of medicine's most urgent challenges.**

Made with 🧬 by [Yuvraj Bhatt](https://github.com/bhattyuvraj22)

[![GitHub stars](https://img.shields.io/github/stars/bhattyuvraj22/antibiotic-resistance-predictor?style=social)](https://github.com/bhattyuvraj22/antibiotic-resistance-predictor)

</div>.
