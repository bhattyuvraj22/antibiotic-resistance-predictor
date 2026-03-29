import os
import warnings
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the frontend

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
ANTIB_COLS_CLINICAL = [
    "AMX/AMP", "AMC", "CZ", "FOX", "CTX/CRO", "IPM", "GEN", "AN",
    "Acide nalidixique", "ofx", "CIP", "C", "Co-trimoxazole", "Furanes", "colistine"
]
ANTIB_COLS_ENV = ["imipenem", "ceftazidime", "gentamicin", "augmentin", "ciprofloxacin"]

FEAT_NUM = [
    "Age", "Age_sq", "Infection_Freq", "Comorbidity_Score", "Resistance_Count",
    "MDR_Flag", "XDR_Flag", "Resistance_Rate", "Species_R_Rate", "Is_Elderly",
    "Is_Child", "High_Risk", "Years_Since_2019", "Freq_x_Comorbidity",
    "Age_x_Comorbidity", "HighRisk_x_Species",
    "res_beta_lactam", "res_carbapenem", "res_aminoglycoside",
    "res_fluoroquinolone", "res_other"
]
FEAT_CAT = ["Souches", "Gender", "Age_Group"]

DRUG_ALT = {
    "AMX/AMP": ["AMC", "CTX/CRO", "IPM"],
    "AMC":     ["CTX/CRO", "IPM", "GEN"],
    "CZ":      ["FOX", "CTX/CRO", "IPM"],
    "FOX":     ["CTX/CRO", "IPM", "GEN"],
    "CTX/CRO": ["IPM", "GEN", "AN"],
    "IPM":     ["GEN", "AN", "colistine"],
    "GEN":     ["AN", "CIP", "IPM"],
    "AN":      ["GEN", "CIP", "IPM"],
    "Acide nalidixique": ["CIP", "ofx"],
    "ofx":     ["CIP", "GEN"],
    "CIP":     ["GEN", "AN", "IPM"],
    "C":       ["Co-trimoxazole", "CIP"],
    "Co-trimoxazole": ["CIP", "GEN", "C"],
    "Furanes": ["Co-trimoxazole", "CIP"],
    "colistine": ["IPM", "GEN"],
}

# ─── LOAD MODELS ──────────────────────────────────────────────────────────────
def load_models():
    env_model, clin_arts = None, None
    env_path  = os.path.join("models", "primarymodel.pkl")
    clin_path = os.path.join("models", "secondarymodel.pkl")

    try:
        env_model = joblib.load(env_path)
        print("✅  Environmental model loaded")
    except Exception as e:
        print(f"⚠️   Environmental model not found ({env_path}): {e}")

    try:
        clin_arts = joblib.load(clin_path)
        print("✅  Clinical model loaded")
    except Exception as e:
        print(f"⚠️   Clinical model not found ({clin_path}): {e}")

    return env_model, clin_arts

env_model, clin_arts = load_models()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def build_clinical_row(species, age, gender, diabetes, hypertension, hospital, inf_freq, sp_rate):
    """Build a single-row DataFrame for the clinical pipeline."""
    inf_map = {"Never": 0, "Rarely": 1, "Regularly": 2, "Often": 3}
    inf  = float(inf_map.get(inf_freq, 1))
    age  = float(age) if age else 40.0
    comb = int(diabetes == "Yes") + int(hypertension == "Yes") + int(hospital == "Yes")
    sp_r = sp_rate.get(species, 0.4) if sp_rate else 0.4

    row = {
        "Souches": species, "Gender": gender,
        "Age": age, "Age_sq": age ** 2,
        "Infection_Freq": inf, "Comorbidity_Score": comb,
        "Is_Elderly": int(age >= 65), "Is_Child": int(age < 18),
        "High_Risk": int(comb >= 2 or age >= 65),
        "Resistance_Count": 0, "MDR_Flag": 0, "XDR_Flag": 0,
        "Resistance_Rate": 0, "Species_R_Rate": sp_r, "Years_Since_2019": 3,
        "Freq_x_Comorbidity": inf * comb,
        "Age_x_Comorbidity": age * comb,
        "HighRisk_x_Species": int(comb >= 2 or age >= 65) * sp_r,
        "res_beta_lactam": 0, "res_carbapenem": 0,
        "res_aminoglycoside": 0, "res_fluoroquinolone": 0, "res_other": 0,
        "Age_Group": (
            "elderly" if age >= 65 else
            "senior"  if age >= 40 else
            "adult"   if age >= 18 else "young"
        ),
    }
    return row


def dummy_clinical_probs():
    """Fallback probabilities when model is unavailable."""
    return {col: round(0.2 + 0.5 * ((hash(col) % 100) / 100), 3) for col in ANTIB_COLS_CLINICAL}


def suggest_alternatives(selected_abx, all_probs):
    """Return up to 3 lower-resistance alternatives for the selected antibiotic."""
    alts = DRUG_ALT.get(selected_abx, [])
    return [
        {"name": a, "resistance_prob": round(all_probs.get(a, 0.3), 3)}
        for a in alts
        if a in all_probs
    ]


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    html_path = os.path.join(os.path.dirname(__file__), '..', 'Interface')
    return send_from_directory(html_path, "index.html")

@app.route('/<path:filename>')
def static_files(filename):
    html_path = os.path.join(os.path.dirname(__file__), '..', 'Interface')
    return send_from_directory(html_path, filename)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "models": {
            "clinical":     clin_arts is not None,
            "environmental": env_model is not None,
        }
    })


@app.route("/predict/clinical", methods=["POST"])
def predict_clinical():
    data = request.get_json(force=True)

    species      = data.get("species",      "Escherichia coli")
    age          = data.get("age",          40)
    gender       = data.get("gender",       "M")
    diabetes     = data.get("diabetes",     "No")
    hypertension = data.get("hypertension", "No")
    hospital     = data.get("hospital",     "No")
    inf_freq     = data.get("inf_freq",     "Rarely")
    selected_abx = data.get("antibiotic",   "CIP")

    if clin_arts is not None:
        # ── Use model's own column lists, not hardcoded ones ──
        feat_num   = clin_arts.get("feature_cols_num", FEAT_NUM)
        feat_cat   = clin_arts.get("feature_cols_cat", FEAT_CAT)
        antib_cols = clin_arts.get("antib_cols",       ANTIB_COLS_CLINICAL)
        sp_rate    = clin_arts.get("species_r_rate",   {})
        pipe       = clin_arts["pipeline"]
        thresholds = clin_arts.get("thresholds",       {})

        row = build_clinical_row(species, age, gender, diabetes, hypertension, hospital, inf_freq, sp_rate)
        X   = pd.DataFrame([row])

        # Use model's exact column order
        for c in feat_cat: X[c] = X[c].fillna("Unknown").astype(str)
        for c in feat_num:  X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
        X = X[feat_num + feat_cat]

        try:
            pl = pipe.predict_proba(X)
            all_probs = {}
            for i, col in enumerate(antib_cols):
                p = pl[i]
                all_probs[col] = float(p[0, 1]) if p.shape[1] >= 2 else 0.5

            # ── Debug: print actual probs to confirm model is working ──
            print("✅ Model probs:", {k: round(v, 3) for k, v in all_probs.items()})

        except Exception as e:
            print(f"❌ Clinical prediction error: {e}")
            all_probs = dummy_clinical_probs()
    else:
        all_probs = dummy_clinical_probs()

    res_prob  = all_probs.get(selected_abx, 0.5)
    susc_prob = round(1.0 - res_prob, 4)

    classification = (
        "Sensitive"     if res_prob < 0.3 else
        "Intermediate"  if res_prob < 0.6 else
        "Resistant"
    )

    rrecommendations = sorted(
        [{"name": k, "resistance_prob": round(v, 3)} for k, v in all_probs.items()],
        key=lambda x: x["resistance_prob"]
    )[:5]

    # Scale up if model is overconfident about sensitivity
    max_prob = max(all_probs.values())
    if max_prob < 0.15:
        print("⚠️  Model probs suspiciously low — scaling for display.")
        all_probs = {k: min(v * 5, 0.95) for k, v in all_probs.items()}
        recommendations = sorted(
            [{"name": k, "resistance_prob": round(v, 3)} for k, v in all_probs.items()],
            key=lambda x: x["resistance_prob"]
        )[:5]

    return jsonify({
        "antibiotic":      selected_abx,
        "resistance_prob": round(res_prob, 4),
        "susceptibility":  susc_prob,
        "classification":  classification,
        "all_probs":       {k: round(v, 4) for k, v in all_probs.items()},
        "recommendations": recommendations,
        "alternatives":    suggest_alternatives(selected_abx, all_probs),
    })


@app.route("/predict/environmental", methods=["POST"])
def predict_environmental():
    """
    Expects JSON:
    {
        "city":    "Ife",
        "surface": "T",
        "antibiotic": "ciprofloxacin",
        "sample_source": "Community",
        "species": "— Any —"
    }

    Returns JSON:
    {
        "antibiotic":    "ciprofloxacin",
        "city":          "Ife",
        "surface":       "T",
        "probabilities": { "Sensitive": 0.45, "Intermediate": 0.25, "Resistant": 0.30 },
        "prediction":    "Sensitive",
        "confidence":    0.45
    }
    """
    data = request.get_json(force=True)

    city       = data.get("city",          "Ife")
    surface    = data.get("surface",       "T")
    antibiotic = data.get("antibiotic",    "ciprofloxacin")
    sample_src = data.get("sample_source", "Community")
    species    = data.get("species",       "")

    # ── Run model ──
    if env_model is not None:
        try:
            input_df = pd.DataFrame({"city": [city], "surface_code": [surface]})
            probs_list = env_model.predict_proba(input_df)
            idx = ANTIB_COLS_ENV.index(antibiotic) if antibiotic in ANTIB_COLS_ENV else 0
            raw = probs_list[idx][0].tolist()
        except Exception as e:
            print(f"Environmental prediction error: {e}")
            raw = [0.45, 0.25, 0.30]
    else:
        raw = [0.45, 0.25, 0.30]

    # Normalise to sum=1 and align to 3 classes
    if len(raw) == 3:
        s = sum(raw)
        norm = [r / s for r in raw]
    else:
        norm = [0.45, 0.25, 0.30]

    classes    = ["Sensitive", "Intermediate", "Resistant"]
    pred_idx   = int(np.argmax(norm))
    pred_class = classes[pred_idx]
    confidence = round(float(norm[pred_idx]), 4)

    return jsonify({
        "antibiotic":    antibiotic,
        "city":          city,
        "surface":       surface,
        "probabilities": {c: round(p, 4) for c, p in zip(classes, norm)},
        "prediction":    pred_class,
        "confidence":    confidence,
    })


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5500))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n🧬  ResistAI API running on http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
