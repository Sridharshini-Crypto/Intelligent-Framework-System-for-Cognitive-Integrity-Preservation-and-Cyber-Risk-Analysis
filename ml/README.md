# ML Experiment Guide

## Objective

Classify URLs as legitimate or phishing using the PhiUSIIL dataset's verified `label` (0 = legitimate, 1 = phishing). The predicted phishing probability is converted to Low, Medium, or High risk for a clear decision-support output.

## Models

1. Random Forest — bagged non-linear ensemble.
2. XGBoost — gradient-boosted decision-tree ensemble.
3. SVM — support-vector classifier with a non-linear decision boundary.

## Run

```powershell
py -m pip install -r requirements.txt
py ml/train_model.py
py ml/test_model.py
py ml/shap_explain.py
```

If `py` is an app-alias rather than a Python installation, install Python 3.11+ from python.org, then run the commands above. Training writes reusable model files and graphs to `artifacts/`, including `model_comparison.png` and `confusion_matrix_comparison.png`. The SHAP script creates a global feature-importance chart and a local explanation for one high-risk test profile.

To open the saved model-comparison graph and combined confusion-matrix image immediately after training, run:

```powershell
python3.13 ml/train_model.py --show
```

## Phishing URL dataset (PhiUSIIL)

The supplied PhiUSIIL dataset is extracted to `data/` and has a verified phishing `label` (0 = legitimate, 1 = phishing). The primary pipeline uses it:

```powershell
python3.13 ml/train_model.py
```

It compares Random Forest, XGBoost, and SVM using a strict **domain-group holdout**: the same domain cannot occur in both the train and held-out test sets. It prints genuine phishing/legitimate confusion matrices, then converts the best model's phishing probability to **Low**, **Medium**, and **High** risk tiers. Outputs are saved in `artifacts/url_risk/`.

## Evaluation policy

Accuracy is measured only on the held-out test split. Do not set or alter results to reach a requested number. With this dataset, 90–98% is not guaranteed: the observed labels and non-leaking features determine the real result. The scripts also report precision, recall, F1, ROC-AUC, and class balance so accuracy is not used in isolation.
