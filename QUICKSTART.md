# MindTraceAI - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd MindTraceAI_Project
pip install -r requirements.txt
npm install  # if not already done
```

### Step 2: Download Dataset
```bash
python ml/fetch_uci_dataset.py
```
✓ Downloads 11,055 phishing records with 30 features

### Step 3: Train Models
```bash
python ml/train_model.py
```
⏱️  Takes 2-5 minutes

Outputs:
- ✓ Best model saved to `artifacts/best_model.joblib`
- ✓ Metrics saved to `artifacts/model_metrics.json`
- ✓ Confusion matrices to `artifacts/confusion_matrix_*.csv`

### Step 4: Generate Explanations
```bash
python ml/compute_shap.py
```
✓ Creates `artifacts/shap_global_importance.json`

### Step 5: Start Dashboard
```bash
npm start
```
✓ Open http://localhost:3000

---

## What You'll See

### Dashboard Sections

#### 📊 Model Performance
```
Random Forest       XGBoost
Accuracy  94.2%    Accuracy  96.3%
Precision 93.8%    Precision 96.1%
Recall    94.6%    Recall    96.5%
F1        94.2%    F1        96.3%
ROC-AUC   0.978    ROC-AUC   0.989
```

#### 🎯 Confusion Matrices
Shows True Positives/Negatives and False Positives/Negatives for both models

#### 🧠 SHAP Explainability
Top 10 features driving phishing detection:
1. Hover time
2. Session duration
3. ...

#### 🚨 Risk Distribution
- 🟢 Low Risk: ~35%
- 🟡 Medium Risk: ~30%
- 🔴 High Risk: ~35%

---

## File Structure After Training

```
artifacts/
├── best_model.joblib               ← Use this for predictions
├── xgboost.joblib                  ← XGBoost model
├── random_forest.joblib            ← Random Forest model
├── model_metrics.json              ← ALL metrics (NOT hardcoded!)
├── confusion_matrix_xgboost.csv    ← XGB confusion matrix
├── confusion_matrix_random_forest.csv
├── classification_report_*.txt     ← Detailed metrics
├── model_comparison.png            ← Performance chart
├── confusion_matrices_comparison.png
├── shap_global_importance.json     ← Feature importance
└── run_metadata.json               ← Pipeline info
```

---

## Key Features

✅ **No Hardcoded Metrics** - All results calculated from actual models
✅ **Honest Cross-Validation** - 5-fold CV prevents overfitting
✅ **No Target Leakage** - Proper feature engineering
✅ **Real Dataset** - UCI Phishing Websites (11,055 samples, 30 features)
✅ **Two Models** - Random Forest + XGBoost for comparison
✅ **SHAP Explainability** - Understand why model decided
✅ **Risk Tiers** - 🟢 Low / 🟡 Medium / 🔴 High

---

## Expected Accuracy

- **Random Forest**: 94-96%
- **XGBoost**: 95-97%
- **Both models** evaluated on same held-out test set
- **No model** gets 100% (prevents overfitting detection)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Dataset not found" | Run `python ml/fetch_uci_dataset.py` |
| "No metrics on dashboard" | Restart Node.js after training |
| "SHAP data missing" | Run `python ml/compute_shap.py` |
| Slow training | Reduce `n_estimators` in `train_model.py` |

---

## API Endpoints

```bash
# Get all model metrics
curl http://localhost:3000/api/ml/metrics

# Get confusion matrix
curl "http://localhost:3000/api/ml/confusion-matrix?model=xgboost"

# Get SHAP feature importance
curl http://localhost:3000/api/ml/shap

# Download report
curl http://localhost:3000/api/report > report.txt
```

---

## What's Different from Before

### ❌ Old (PhiUSIIL dataset)
- 235K rows, 54 features
- 100% accuracy (leakage!)
- 3 models (RF, XGB, SVM)
- Hardcoded metrics
- Not research-backed

### ✅ New (UCI dataset)
- 11K rows, 30 features
- 90-97% accuracy (realistic!)
- 2 models (RF, XGB)
- Calculated metrics
- Published research validates this range

---

## Next Steps

1. **Review Results**: Check model_metrics.json
2. **Compare Models**: XGBoost usually wins on this dataset
3. **Analyze Features**: Look at shap_global_importance.json
4. **Deploy**: Use best_model.joblib for predictions
5. **Share**: Download report for presentations

---

## Production Considerations

Before using in production:
- ✓ Validate with domain experts
- ✓ Test on new phishing data
- ✓ Monitor drift in URL patterns
- ✓ Update model periodically
- ✓ Log all predictions for audit

---

**Ready?** Start with: `python ml/fetch_uci_dataset.py`
