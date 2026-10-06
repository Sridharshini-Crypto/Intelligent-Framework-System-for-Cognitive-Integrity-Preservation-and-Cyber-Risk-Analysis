# MindTraceAI — Cognitive Integrity Preservation System

A local-first phishing-awareness dashboard built from `phishing_awareness_dataset.csv`. It presents behavioural analytics, an explainable personal risk check, and awareness guidance.

## Run locally

1. Open a terminal in this folder.
2. Run `npm start`.
3. Visit `http://localhost:3000`.

No package installation is required for the dashboard. The CSV stays local and is read by the Node.js server at startup.

## Machine-learning implementation

The `ml/` directory provides reproducible training, test, inference, and explainability scripts. It compares **Random Forest, XGBoost, and SVM**, selects the best model by held-out F1, then writes accuracy, precision, recall, F1, ROC-AUC, confusion matrices, and a comparison graph to `artifacts/`. The SHAP layer produces global feature importance, positive/negative local factors, and a risk recommendation.

```powershell
py -m pip install -r requirements.txt
py ml/train_model.py
py ml/test_model.py
py ml/shap_explain.py
```

See `docs/literature_survey.md` for the literature survey, research gaps, limitations, and 11 APA-formatted references.

## Important interpretation

The supplied dataset contains interaction behaviour (`clicked_link`, `reported_email`, hover time, etc.) but no confirmed phishing/non-phishing label. The dashboard therefore provides an explainable **cognitive-risk score** for awareness and intervention prioritisation; it does not claim to classify an email as phishing.
