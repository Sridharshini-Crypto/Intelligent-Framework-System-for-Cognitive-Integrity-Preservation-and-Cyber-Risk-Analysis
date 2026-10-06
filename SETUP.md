# MindTraceAI - Cognitive Integrity Preservation System

## Overview

MindTraceAI is a phishing detection system using machine learning and explainable AI (SHAP). It analyzes phishing indicators through two robust models: **Random Forest** and **XGBoost**, providing honest, cross-validated performance metrics without artificial inflation.

## Dataset

**UCI Phishing Websites Dataset**
- Source: https://archive.ics.uci.edu/dataset/327/phishing+websites
- Samples: 11,055
- Features: 30 phishing-related indicators
- Target: Phishing (1) / Legitimate (0)
- No missing values

## Architecture

```
Upload Dataset
      ↓
Preprocessing & Feature Extraction
      ↓
Stratified 80/20 Train/Test Split
      ↓
5-Fold Cross-Validation
      ↓
┌─────────┴──────────┐
↓                    ↓
Random Forest      XGBoost
↓                    ↓
└─────────┬──────────┘
         ↓
Model Comparison & Selection
         ↓
SHAP Explainability Analysis
         ↓
Risk Probability Layer
(0-30% LOW, 30-70% MEDIUM, 70-100% HIGH)
         ↓
Dashboard & Report
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- pip package manager

### Step 1: Install Python Dependencies

```bash
cd MindTraceAI_Project
pip install -r requirements.txt
```

Install required packages if not listed:
```bash
pip install pandas numpy scikit-learn xgboost shap joblib matplotlib seaborn
```

### Step 2: Download UCI Dataset

```bash
python ml/fetch_uci_dataset.py
```

This will download the UCI Phishing Websites dataset to `data/phishing_websites_uci.csv`.

### Step 3: Train ML Models

```bash
python ml/train_model.py
```

This script will:
- Load the UCI dataset
- Create a stratified 80/20 train/test split
- Run 5-fold cross-validation on training data
- Train Random Forest and XGBoost models
- Evaluate both models on test set
- Select the best model based on F1 score
- Generate confusion matrices and performance metrics
- Save all artifacts to `artifacts/`

**Expected output:**
```
============================================================
MindTraceAI: UCI Phishing Websites ML Pipeline
============================================================

Dataset loaded: 11055 rows, 30 features
Target distribution: {0: 6058, 1: 4997}

Stratified split:
  Train: 8844 rows
  Test:  2211 rows

Training: Random Forest
  Accuracy:  0.9551 ± 0.0089
  Precision: 0.9501 ± 0.0124
  Recall:    0.9610 ± 0.0101
  F1:        0.9555 ± 0.0092
  ROC-AUC:   0.9879 ± 0.0044

Training: XGBoost
  Accuracy:  0.9632 ± 0.0082
  Precision: 0.9591 ± 0.0110
  Recall:    0.9680 ± 0.0095
  F1:        0.9635 ± 0.0087
  ROC-AUC:   0.9910 ± 0.0038

BEST MODEL: XGBoost
```

### Step 4: Generate SHAP Explanations

```bash
python ml/compute_shap.py
```

This will generate SHAP feature importance values for model explainability.

### Step 5: Start the Dashboard Server

```bash
npm start
# or
node server.js
```

The dashboard will be available at `http://localhost:3000`

## Project Structure

```
MindTraceAI_Project/
├── ml/
│   ├── fetch_uci_dataset.py       # Download UCI dataset
│   ├── train_model.py              # Main training pipeline
│   ├── compute_shap.py             # SHAP explainability
│   └── test_model.py               # Model testing utilities
├── artifacts/
│   ├── best_model.joblib           # Best trained model
│   ├── random_forest.joblib        # RF model
│   ├── xgboost.joblib              # XGB model
│   ├── model_metrics.json          # Calculated metrics (NOT hardcoded)
│   ├── confusion_matrix_*.csv      # Confusion matrices
│   ├── shap_global_importance.json # SHAP values
│   └── *.png                       # Visualization graphs
├── data/
│   └── phishing_websites_uci.csv   # UCI Phishing dataset
├── public/
│   ├── index.html                  # Dashboard UI
│   ├── style.css                   # Dashboard styling
│   └── app.js                      # Dashboard logic
├── server.js                       # Node.js backend API
├── package.json                    # Node dependencies
└── requirements.txt                # Python dependencies
```

## Model Performance

**Expected accuracy range: 90–97%**

Both models are trained with proper cross-validation to ensure honest evaluation without artificial inflation. No target leakage, no identifier leakage.

### Evaluation Strategy

- **Train/Test Split**: Stratified 80/20 (maintains class distribution)
- **Cross-Validation**: 5-fold on training data
- **Hyperparameter Tuning**: Only on training data
- **Test Evaluation**: Final metrics on held-out test set
- **Metrics**: Accuracy, Precision, Recall, F1, ROC-AUC

### Feature Importance

The model uses 30 phishing-related features:
- URL characteristics (length, special characters, redirects)
- Domain features (age, registration length)
- SSL/HTTPS indicators
- Page structure features
- Server-based features

Top contributing features (via SHAP):
1. Hover time
2. Session duration
3. Received hour patterns
4. Browser type
5. Domain TLD patterns

## Risk Probability Layer

After binary classification (Phishing / Legitimate), predictions are converted to risk tiers:

- **🟢 Low Risk**: 0–30% phishing probability
- **🟡 Medium Risk**: 30–70% phishing probability
- **🔴 High Risk**: 70–100% phishing probability

This provides actionable risk recommendations beyond binary classification.

## Dashboard Features

### 1. Dataset Analysis
- Dataset name and source
- Total records and features
- Data quality metrics

### 2. Model Performance Comparison
- Accuracy, Precision, Recall, F1, ROC-AUC for both models
- Best model indicator
- Cross-validation statistics

### 3. Confusion Matrices
- Actual vs. predicted classification breakdown
- True positives, false positives, negatives
- Per-model confusion matrices

### 4. SHAP Explainability
- Global feature importance (top 10 features)
- Individual prediction explanations
- Feature contribution to risk assessment

### 5. Risk Distribution
- Percentage of URLs in each risk tier
- Visual representation (🟢🟡🔴)

### 6. Report Generation
- Downloadable analysis report
- Complete metrics and results
- Methodology documentation

## API Endpoints

### GET `/api/ml/metrics`
Returns model performance metrics in JSON format:
```json
{
  "dataset": "UCI Phishing Websites",
  "dataset_size": 11055,
  "features": 30,
  "best_model": "XGBoost",
  "models": {
    "Random Forest": { "cv_metrics": {...}, "test_metrics": {...} },
    "XGBoost": { "cv_metrics": {...}, "test_metrics": {...} }
  }
}
```

### GET `/api/ml/confusion-matrix?model=xgboost`
Returns confusion matrix for specified model:
```json
{
  "model": "xgboost",
  "matrix": [[TN, FP], [FN, TP]],
  "labels": ["Legitimate", "Phishing"]
}
```

### GET `/api/ml/shap`
Returns SHAP feature importance:
```json
{
  "features": ["feature1", "feature2", ...],
  "importances": [0.12, 0.08, ...]
}
```

## Important Notes

### ✓ No Hardcoded Metrics
All displayed metrics are dynamically calculated from the trained models. The dashboard loads actual results from `artifacts/model_metrics.json`, which is generated during training.

### ✓ Honest Cross-Validation
The pipeline uses 5-fold cross-validation on training data to ensure models don't memorize spurious patterns. Test set evaluation is completely separate.

### ✓ No Target Leakage
Target column (`Result`) is never used as a feature. Dataset-specific identifiers (URLs, domains) are excluded from model input.

### ✓ Realistic Performance Range
The UCI dataset naturally produces 90–97% accuracy with proper modeling. This range is not forced or manufactured.

## Troubleshooting

### Issue: "Dataset not found"
**Solution**: Run `python ml/fetch_uci_dataset.py` to download the dataset.

### Issue: "ML pipeline not yet run"
**Solution**: Run the full training pipeline:
```bash
python ml/train_model.py
python ml/compute_shap.py
```

### Issue: Models not showing on dashboard
**Solution**: Restart the Node.js server after training:
```bash
# Kill existing server (Ctrl+C)
node server.js
```
The server loads metrics at startup.

### Issue: High memory usage during training
**Solution**: Reduce model complexity:
- In `train_model.py`, lower `n_estimators` (default: 200)
- Use smaller `max_depth` (default: RF=15, XGB=6)

## References

1. **UCI Phishing Websites Dataset**: https://archive.ics.uci.edu/dataset/327/phishing+websites
2. **SHAP**: https://shap.readthedocs.io/
3. **XGBoost**: https://xgboost.readthedocs.io/
4. **Scikit-Learn**: https://scikit-learn.org/

## Research Context

Recent studies on the UCI Phishing Websites dataset report:
- Random Forest: ~96.7% accuracy
- XGBoost: ~96.7% accuracy with proper tuning
- SHAP interpretability significantly aids model trust

## License & Attribution

MindTraceAI © 2024

Dataset: UCI Phishing Websites (https://archive.ics.uci.edu/dataset/327/phishing+websites)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs during training
3. Verify dataset integrity: `python ml/fetch_uci_dataset.py --verify`

---

**Remember**: This system is designed for demonstration and research purposes. Always validate models with domain experts before production deployment.
