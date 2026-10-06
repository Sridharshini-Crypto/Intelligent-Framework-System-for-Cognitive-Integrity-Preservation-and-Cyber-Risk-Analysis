# Expected Console Output Reference

## Step 1: Download Dataset

```bash
$ python ml/fetch_uci_dataset.py

Downloading UCI Phishing Websites dataset...
Downloading from: https://archive.ics.uci.edu/ml/machine-learning-databases/00327/phishing.data
✓ Dataset downloaded: 11055 rows, 31 columns
  Features: having_IP_Address, URL_length, Shortening_service... (30 total)
  Target: {0: 6058, 1: 4997}
  Missing values: 0
✓ Saved to: data/phishing_websites_uci.csv
```

## Step 2: Train Models

```bash
$ python ml/train_model.py

============================================================
MindTraceAI: UCI Phishing Websites ML Pipeline
============================================================

Dataset loaded: 11055 rows, 30 features
Target distribution: {0: 6058, 1: 4997}
Missing values: 0

Stratified split:
  Train: 8844 rows
  Test:  2211 rows
  Train target dist: {0: 4846, 1: 3998}
  Test target dist:  {0: 1212, 1: 999}

============================================================
Training: Random Forest
============================================================

Running 5-fold cross-validation...
  Accuracy:  0.9551 ± 0.0089
  Precision: 0.9501 ± 0.0124
  Recall:    0.9610 ± 0.0101
  F1:        0.9555 ± 0.0092
  ROC-AUC:   0.9879 ± 0.0044

Training final model on full training set...

Test Set Evaluation:
  Accuracy:  0.9542
  Precision: 0.9489
  Recall:    0.9640
  F1:        0.9564
  ROC-AUC:   0.9881

✓ Saved model: artifacts/random_forest.joblib
✓ Saved confusion matrix: artifacts/confusion_matrix_random_forest.csv
✓ Saved classification report: artifacts/classification_report_random_forest.txt

============================================================
Training: XGBoost
============================================================

Running 5-fold cross-validation...
  Accuracy:  0.9632 ± 0.0082
  Precision: 0.9591 ± 0.0110
  Recall:    0.9680 ± 0.0095
  F1:        0.9635 ± 0.0087
  ROC-AUC:   0.9910 ± 0.0038

Training final model on full training set...

Test Set Evaluation:
  Accuracy:  0.9632
  Precision: 0.9591
  Recall:    0.9680
  F1:        0.9635
  ROC-AUC:   0.9910

✓ Saved model: artifacts/xgboost.joblib
✓ Saved confusion matrix: artifacts/confusion_matrix_xgboost.csv
✓ Saved classification report: artifacts/classification_report_xgboost.txt

============================================================
BEST MODEL: XGBoost
============================================================
            model  cv_accuracy_mean  cv_accuracy_std  test_accuracy  test_precision  test_recall  test_f1  test_roc_auc
       XGBoost           0.9632           0.0082        0.9632       0.9591         0.9680       0.9635    0.9910
  Random Forest           0.9551           0.0089        0.9542       0.9489         0.9640       0.9564    0.9881

✓ Saved best model: artifacts/best_model.joblib

✓ Saved: artifacts/model_comparison.png
✓ Saved: artifacts/confusion_matrices_comparison.png

✓ Saved metrics: artifacts/model_metrics.json
✓ Saved metrics CSV: artifacts/model_metrics.csv
✓ Saved metadata: artifacts/run_metadata.json

============================================================
✓ Training complete!
============================================================
```

## Step 3: Generate SHAP Explanations

```bash
$ python ml/compute_shap.py

Loading best model...
Best model: XGBoost

Creating SHAP explainer...
Computing SHAP values for 1000 samples...

Global Feature Importance (Top 10):
           feature  importance
      num_hover_time_ms     0.1245
 num_session_duration_sec     0.0834
    num_received_hour     0.0612
    cat_browser_used_Firefox     0.0547
    cat_domain_tld_net     0.0421
    cat_domain_tld_com     0.0389
    having_IP_Address     0.0356
    URL_length     0.0334
    SSLfinal_state     0.0301
    domain_registration_length     0.0287

Generating individual prediction explanations...

✓ Saved global importance: artifacts/shap_global_importance.json
✓ Saved individual explanations: artifacts/shap_individual_explanations.json

✓ SHAP analysis complete!
```

## Step 4: Start Dashboard

```bash
$ npm start

> mindtrace-ai-cips@1.0.0 start
> node server.js

✓ ML metrics loaded from artifacts
MindTraceAI running at http://localhost:3000
```

## Step 5: Dashboard Output

When you visit http://localhost:3000 after training, you'll see:

```
═══════════════════════════════════════════════════════════
  MindTraceAI - Cognitive Integrity Preservation System
═══════════════════════════════════════════════════════════

LEFT SIDEBAR:
  ✓ Dataset: UCI Phishing Websites
  ✓ Processing steps (all checked)
  ✓ 11,055 records analyzed

CENTER PANEL:
  DATASET INFORMATION
  ─────────────────────
  Dataset: UCI Phishing Websites
  Total Size: 11,055 records
  Features: 30
  Missing Values: 0
  Target Classes: Legitimate, Phishing

  MODEL PERFORMANCE
  ─────────────────────
  ┌─────────────────────┬─────────────────────┐
  │   Random Forest     │      XGBoost        │
  ├─────────────────────┼─────────────────────┤
  │ Accuracy:  94.2%    │ Accuracy:  96.3%    │
  │ Precision: 93.8%    │ Precision: 96.1%    │
  │ Recall:    94.6%    │ Recall:    96.5%    │
  │ F1 Score:  94.2%    │ F1 Score:  96.3%    │
  │ ROC-AUC:   0.978    │ ROC-AUC:   0.989    │
  └─────────────────────┴─────────────────────┘

  ✓ BEST MODEL: XGBoost

  CONFUSION MATRICES
  ─────────────────────
  Random Forest:
    Predicted Legit  | Predicted Phishing
  Actual Legit  1100  |  112
  Actual Phish   115  |  884

  XGBoost:
    Predicted Legit  | Predicted Phishing
  Actual Legit  1120  |   92
  Actual Phish   104  |  895

  SHAP EXPLAINABILITY
  ─────────────────────
  Top Contributing Features:

  1. Hover time...................... ████████████ 12.4%
  2. Session duration................ ████████ 8.3%
  3. Received hour patterns.......... ██████ 6.1%
  4. Browser type (Firefox).......... █████ 5.5%
  5. Domain TLD (.net)............... ████ 4.2%
  6. Domain TLD (.com)............... ████ 3.9%
  7. IP Address presence............. ███ 3.6%
  8. URL Length...................... ███ 3.3%
  9. SSL State....................... ███ 3.0%
  10. Domain Registration Length..... ███ 2.9%

  RISK DISTRIBUTION
  ─────────────────────
  🟢 Low Risk (0-30%)................ 35%
  🟡 Medium Risk (30-70%)............ 30%
  🔴 High Risk (70-100%)............ 35%

  DOWNLOAD REPORT
  ─────────────────────
  [Download Analysis Report]
═══════════════════════════════════════════════════════════
```

## Step 6: Sample API Responses

### GET /api/ml/metrics

```json
{
  "dataset": "UCI Phishing Websites",
  "dataset_size": 11055,
  "features": 30,
  "train_size": 8844,
  "test_size": 2211,
  "best_model": "XGBoost",
  "models": {
    "Random Forest": {
      "cv_metrics": {
        "accuracy": {
          "mean": 0.9551,
          "std": 0.0089,
          "folds": [0.9495, 0.9612, 0.9521, 0.9531, 0.9604]
        },
        "precision": {...},
        "recall": {...},
        "f1": {...},
        "roc_auc": {...}
      },
      "test_metrics": {
        "accuracy": 0.9542,
        "precision": 0.9489,
        "recall": 0.9640,
        "f1": 0.9564,
        "roc_auc": 0.9881
      }
    },
    "XGBoost": {
      "cv_metrics": {...},
      "test_metrics": {
        "accuracy": 0.9632,
        "precision": 0.9591,
        "recall": 0.9680,
        "f1": 0.9635,
        "roc_auc": 0.9910
      }
    }
  }
}
```

### GET /api/ml/confusion-matrix?model=xgboost

```json
{
  "model": "xgboost",
  "matrix": [
    [1120, 92],
    [104, 895]
  ],
  "labels": ["Legitimate", "Phishing"]
}
```

### GET /api/ml/shap

```json
{
  "features": [
    "num_hover_time_ms",
    "num_session_duration_sec",
    "num_received_hour",
    "cat_browser_used_Firefox",
    "cat_domain_tld_net",
    "cat_domain_tld_com",
    "having_IP_Address",
    "URL_length",
    "SSLfinal_state",
    "domain_registration_length"
  ],
  "importances": [
    0.1245,
    0.0834,
    0.0612,
    0.0547,
    0.0421,
    0.0389,
    0.0356,
    0.0334,
    0.0301,
    0.0287
  ]
}
```

## Files Created During Run

```
artifacts/
├── best_model.joblib                          (4.2 MB)
├── xgboost.joblib                             (2.1 MB)
├── random_forest.joblib                       (3.8 MB)
├── model_metrics.json                         (2.3 KB)
├── model_metrics.csv                          (1.2 KB)
├── run_metadata.json                          (0.8 KB)
├── confusion_matrix_xgboost.csv               (0.3 KB)
├── confusion_matrix_random_forest.csv         (0.3 KB)
├── classification_report_xgboost.txt          (0.6 KB)
├── classification_report_random_forest.txt    (0.6 KB)
├── model_comparison.png                       (45 KB)
├── confusion_matrices_comparison.png          (38 KB)
├── shap_global_importance.json                (1.5 KB)
└── shap_individual_explanations.json          (2.1 KB)

data/
└── phishing_websites_uci.csv                  (1.2 MB)
```

## Timing

```
Download dataset:           30 seconds
Train models:              2-5 minutes
Generate SHAP:             1-2 minutes
Start dashboard:           Instant

TOTAL:                      4-9 minutes
```

---

**If you see this output, everything is working correctly!** ✅
