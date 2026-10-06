"""SHAP Explainability for MindTraceAI Best Model

Computes SHAP values for global and individual prediction explanations.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
import shap
import warnings

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'phishing_websites_uci.csv'
OUT = ROOT / 'artifacts'


def compute_shap_explanations():
    """Compute SHAP values for the best model."""
    
    # Load data
    df = pd.read_csv(DATA)
    X = df.drop(columns=['Result'])
    y = df['Result'].astype(int)
    
    print("Loading best model...")
    best_model_path = OUT / 'best_model.joblib'
    if not best_model_path.exists():
        raise FileNotFoundError(
            f"Best model not found: {best_model_path}\n"
            "Please run: python ml/train_model.py"
        )
    
    best_model = joblib.load(best_model_path)
    
    # Load metrics to get best model name
    metrics_path = OUT / 'model_metrics.json'
    with open(metrics_path) as f:
        metrics = json.load(f)
    best_model_name = metrics['best_model']
    
    print(f"Best model: {best_model_name}")
    
    # Create SHAP explainer
    print(f"\nCreating SHAP explainer...")
    
    # best_model is a raw tree-based estimator (no pipeline wrapper),
    # so it can be passed directly to shap.TreeExplainer.
    explainer = shap.TreeExplainer(best_model)

    # Compute SHAP values for a sample (to keep computation reasonable)
    sample_size = min(1000, len(X))
    X_sample = X.iloc[:sample_size]

    # No preprocessing pipeline to run - model consumes raw features directly.
    X_sample_transformed = X_sample
    
    print(f"Computing SHAP values for {sample_size} samples...")
    shap_values = explainer.shap_values(X_sample_transformed)
    
    # Handle output format
    if isinstance(shap_values, list):
        # Binary classification - take class 1 (phishing)
        shap_values = shap_values[1]
    
    # Global feature importance (mean absolute SHAP value)
    global_importance = np.abs(shap_values).mean(axis=0)
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': global_importance
    }).sort_values('importance', ascending=False)
    
    print("\nGlobal Feature Importance (Top 10):")
    print(feature_importance.head(10).to_string(index=False))
    
    # Save global importance
    global_importance_data = {
        'features': feature_importance['feature'].tolist(),
        'importances': feature_importance['importance'].tolist()
    }
    
    global_importance_path = OUT / 'shap_global_importance.json'
    with open(global_importance_path, 'w') as f:
        json.dump(global_importance_data, f, indent=2)
    print(f"\n✓ Saved global importance: {global_importance_path}")
    
    # Individual prediction explanations for high-risk phishing samples
    print("\nGenerating individual prediction explanations...")
    
    # Get predictions
    y_pred_proba = best_model.predict_proba(X)[:, 1]
    
    # Find high-risk phishing and legitimate samples
    high_risk_indices = np.argsort(y_pred_proba)[-5:]  # Top 5 phishing
    low_risk_indices = np.argsort(y_pred_proba)[:5]     # Bottom 5 legitimate
    
    individual_explanations = {
        'high_risk_phishing': [],
        'low_risk_legitimate': []
    }
    
    # High-risk phishing explanations
    for idx in high_risk_indices:
        X_instance = X.iloc[idx:idx+1]
        X_instance_transformed = X_instance
        shap_val = explainer.shap_values(X_instance_transformed)
        
        if isinstance(shap_val, list):
            shap_val = shap_val[1]
        
        # Get top contributing features
        top_features_idx = np.argsort(np.abs(shap_val[0]))[-5:][::-1]
        
        explanation = {
            'phishing_probability': float(y_pred_proba[idx]),
            'top_features': [
                {
                    'name': X.columns[i],
                    'shap_value': float(shap_val[0][i]),
                    'feature_value': float(X.iloc[idx, i])
                }
                for i in top_features_idx
            ]
        }
        individual_explanations['high_risk_phishing'].append(explanation)
    
    # Low-risk legitimate explanations
    for idx in low_risk_indices:
        X_instance = X.iloc[idx:idx+1]
        X_instance_transformed = X_instance
        shap_val = explainer.shap_values(X_instance_transformed)
        
        if isinstance(shap_val, list):
            shap_val = shap_val[1]
        
        # Get top contributing features
        top_features_idx = np.argsort(np.abs(shap_val[0]))[-5:][::-1]
        
        explanation = {
            'phishing_probability': float(y_pred_proba[idx]),
            'top_features': [
                {
                    'name': X.columns[i],
                    'shap_value': float(shap_val[0][i]),
                    'feature_value': float(X.iloc[idx, i])
                }
                for i in top_features_idx
            ]
        }
        individual_explanations['low_risk_legitimate'].append(explanation)
    
    # Save individual explanations
    individual_path = OUT / 'shap_individual_explanations.json'
    with open(individual_path, 'w') as f:
        json.dump(individual_explanations, f, indent=2)
    print(f"✓ Saved individual explanations: {individual_path}")
    
    print(f"\n✓ SHAP analysis complete!")


if __name__ == "__main__":
    compute_shap_explanations()
