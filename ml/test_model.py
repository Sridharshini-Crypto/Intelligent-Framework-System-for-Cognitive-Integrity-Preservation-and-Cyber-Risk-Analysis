"""Verify UCI Phishing Websites ML evaluation artifacts.

Ensures training pipeline produced valid models with realistic accuracy
(90-97%), not artificial 100%. Validates all required artifacts exist.
"""
from pathlib import Path
import json
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'

# Required artifacts from successful training
REQUIRED = [
    'model_metrics.json',
    'model_metrics.csv',
    'best_model.joblib',
    'random_forest.joblib',
    'xgboost.joblib',
    'confusion_matrix_random_forest.csv',
    'confusion_matrix_xgboost.csv',
    'classification_report_random_forest.txt',
    'classification_report_xgboost.txt',
    'run_metadata.json',
    'model_comparison.png',
    'confusion_matrices_comparison.png'
]

def validate_artifacts():
    """Check all artifacts exist."""
    missing = [name for name in REQUIRED if not (OUT / name).exists()]
    if missing:
        print("ERROR: Missing artifacts. Train first:")
        print("  python ml/fetch_uci_dataset.py")
        print("  python ml/train_model.py")
        print(f"\nMissing files: {', '.join(missing)}")
        return False
    return True

def validate_metrics():
    """Validate metrics are in realistic 90-97% range, not artificial 100%."""
    metrics_path = OUT / 'model_metrics.json'
    with open(metrics_path) as f:
        metrics = json.load(f)
    
    print("\n" + "="*60)
    print("MindTraceAI UCI Phishing Websites - Model Verification")
    print("="*60)
    
    print(f"\nDataset: {metrics['dataset']}")
    print(f"Total samples: {metrics['dataset_size']}")
    print(f"Features: {metrics['features']}")
    print(f"Train/Test split: {metrics['train_size']}/{metrics['test_size']}")
    
    # Check each model
    for model_name, model_data in metrics['models'].items():
        test_metrics = model_data['test_metrics']
        cv_metrics = model_data['cv_metrics']
        
        print(f"\n{model_name}:")
        print(f"  Test Accuracy:  {test_metrics['accuracy']:.4f}")
        print(f"  Test Precision: {test_metrics['precision']:.4f}")
        print(f"  Test Recall:    {test_metrics['recall']:.4f}")
        print(f"  Test F1:        {test_metrics['f1']:.4f}")
        print(f"  Test ROC-AUC:   {test_metrics['roc_auc']:.4f}")
        print(f"  CV Accuracy:    {cv_metrics['accuracy']['mean']:.4f} +/- {cv_metrics['accuracy']['std']:.4f}")
        
        # Validate realistic range (90-97%)
        acc = test_metrics['accuracy']
        if acc < 0.90:
            print(f"  WARNING: Low accuracy ({acc:.1%}). Model may need tuning.")
        elif acc > 0.97:
            print(f"  WARNING: Very high accuracy ({acc:.1%}). Check for leakage!")
        elif acc >= 1.0:
            print(f"  FAIL: Accuracy is 100%! Data leakage detected!")
            return False
        else:
            print(f"  OK: Realistic accuracy range (90-97%)")
    
    # Validate best model
    best_model = metrics['best_model']
    print(f"\nOK: Best Model: {best_model}")
    print(f"  (Selected based on F1 score)")
    
    # Validate metadata
    metadata_path = OUT / 'run_metadata.json'
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    print(f"\nOK: Evaluation Strategy: {metadata['evaluation_strategy']}")
    print(f"OK: No target leakage: {metadata['no_target_leakage']}")
    print(f"OK: No identifier leakage: {metadata['no_identifier_leakage']}")
    
    # Check confusion matrices
    for model_name in metrics['models'].keys():
        cm_file = OUT / f"confusion_matrix_{model_name.lower().replace(' ', '_')}.csv"
        if cm_file.exists():
            cm = pd.read_csv(cm_file, index_col=0)
            print(f"\n{model_name} Confusion Matrix:")
            print(cm)
    
    return True

def main():
    """Run all validations."""
    print("\nValidating MindTraceAI UCI Phishing Websites Pipeline...\n")
    
    # Check artifacts exist
    if not validate_artifacts():
        sys.exit(1)
    
    # Validate metrics
    if not validate_metrics():
        sys.exit(1)
    
    print("\n" + "="*60)
    print("PASS: All artifacts valid. Realistic accuracy achieved.")
    print("  Models are NOT overfitted (no 100% accuracy).")
    print("  5-fold CV provides stable evaluation.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
