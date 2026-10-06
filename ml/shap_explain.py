"""SHAP explainability for the trained PhiUSIIL URL phishing model."""
from pathlib import Path
import json
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import shap
from sklearn.model_selection import train_test_split
from train_url_risk_model import DATA, OUT, SEED, prepare, tier

def main():
    model_file = OUT / "best_url_risk_model.joblib"
    if not model_file.exists(): raise SystemExit("Train first: python3.13 ml/train_model.py")
    raw = pd.read_csv(DATA, low_memory=False)
    # Match the training sample and split so the explanation is reproducible.
    if len(raw) > 30000: raw, _ = train_test_split(raw, train_size=30000, stratify=raw["label"], random_state=SEED)
    X, _, _ = prepare(raw)
    _, test = train_test_split(X, test_size=.20, stratify=raw["label"], random_state=SEED)
    pipeline = joblib.load(model_file); prep = pipeline.named_steps["preprocess"]; model = pipeline.named_steps["model"]
    background = prep.transform(test.iloc[:80]); explained = prep.transform(test.iloc[:30]); names = prep.get_feature_names_out()
    explainer = shap.KernelExplainer(model.predict_proba, background)
    values = explainer.shap_values(explained, nsamples=100)
    if isinstance(values, list): values = values[1]
    elif getattr(values, "ndim", 0) == 3: values = values[:, :, 1]
    importance = pd.Series(abs(values).mean(axis=0), index=names).sort_values(ascending=True)
    plt.figure(figsize=(9, 7)); importance.tail(15).plot.barh(color="#39756e"); plt.title("MindTraceAI: global SHAP feature importance"); plt.xlabel("Mean |SHAP value|"); plt.tight_layout(); plt.savefig(OUT / "shap_global_feature_importance.png", dpi=180); plt.close()
    probabilities = model.predict_proba(explained)[:, 1]; idx = int(probabilities.argmax()); local = pd.Series(values[idx], index=names).sort_values()
    plt.figure(figsize=(9, 7)); local.tail(12).plot.barh(color="#c76053"); plt.title("MindTraceAI: positive phishing-risk contributors"); plt.xlabel("SHAP contribution"); plt.tight_layout(); plt.savefig(OUT / "shap_local_explanation.png", dpi=180); plt.close()
    factors=[{"feature":k,"direction":"increases phishing risk" if v>0 else "reduces phishing risk","shap_value":round(float(v),4)} for k,v in local.reindex(local.abs().sort_values(ascending=False).index).head(8).items()]
    probability=float(probabilities[idx]); result={"prediction":"Phishing" if probability>=.5 else "Legitimate","phishing_probability":round(probability,4),"risk_level":tier(probability),"key_contributing_factors":factors,"recommendation":"Block and investigate this URL before use." if probability>=.66 else "Review URL/domain indicators before proceeding." if probability>=.33 else "Low predicted risk; continue normal verification."}
    (OUT / "shap_risk_recommendation.json").write_text(json.dumps(result, indent=2)); print(json.dumps(result, indent=2)); print("SHAP graphs saved to", OUT)

if __name__ == "__main__": main()
