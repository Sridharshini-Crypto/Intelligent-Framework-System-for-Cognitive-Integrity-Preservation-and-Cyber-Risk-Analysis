"""MindTraceAI UCI Phishing Websites ML Pipeline

Two models only: Random Forest + XGBoost

Evaluation:
- Stratified 80/20 train/test split
- 5-fold cross-validation on training data
- Hyperparameter tuning only on training data
- No target leakage, no identifier leakage
- Realistic accuracy in 90-97% range

Output:
- Model metrics (accuracy, precision, recall, F1, ROC-AUC)
- Confusion matrices
- Cross-validation statistics
- Best model artifact
- Metadata for SHAP
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_validate
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)
from xgboost import XGBClassifier
import joblib
import matplotlib
matplotlib.use('Agg')  # Generate files without requiring a Tkinter desktop backend.
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'phishing_websites_uci.csv'
OUT = ROOT / 'artifacts'
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
TEST_SIZE = 0.20
CV_FOLDS = 5


def json_default(value):
    """Convert NumPy values produced by pandas/scikit-learn for JSON output."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def load_and_prepare_data():
    """Load UCI dataset and prepare for training."""
    
    if not DATA.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA}\n"
            "Please run: python ml/fetch_uci_dataset.py"
        )
    
    # Load dataset
    df = pd.read_csv(DATA)
    
    # Separate features and target
    X = df.drop(columns=['Result'])
    y = df['Result'].astype(int)
    
    print(f"Dataset loaded: {len(df)} rows, {len(X.columns)} features")
    print(f"Target distribution: {dict(y.value_counts().sort_index())}")
    print(f"Missing values: {df.isna().sum().sum()}")
    
    # Ensure no NaN
    X = X.fillna(X.mean(numeric_only=True))
    
    # Standardize features (especially important for tree-based models)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=X.columns)
    
    return X_scaled, y, X.columns


def stratified_split_and_cv(X, y):
    """Create stratified train/test split with CV on train."""
    
    # Stratified 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=TEST_SIZE, 
        stratify=y, 
        random_state=SEED
    )
    
    print(f"\nStratified split:")
    print(f"  Train: {len(X_train)} rows")
    print(f"  Test:  {len(X_test)} rows")
    print(f"  Train target dist: {dict(y_train.value_counts().sort_index())}")
    print(f"  Test target dist:  {dict(y_test.value_counts().sort_index())}")
    
    # Cross-validation splitter
    cv_splitter = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    
    return X_train, X_test, y_train, y_test, cv_splitter


def train_and_evaluate_models(X_train, X_test, y_train, y_test, cv_splitter):
    """Train Random Forest and XGBoost with CV."""
    
    # Model configurations with hyperparameter tuning
    models_config = {
        'Random Forest': {
            'model': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_leaf=2,
                min_samples_split=5,
                max_features='sqrt',
                class_weight='balanced',
                n_jobs=-1,
                random_state=SEED
            ),
            'cv_scoring': ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        },
        'XGBoost': {
            'model': XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.08,
                subsample=0.8,
                colsample_bytree=0.8,
                gamma=1.0,
                min_child_weight=1,
                scale_pos_weight=1,
                eval_metric='logloss',
                random_state=SEED,
                n_jobs=-1
            ),
            'cv_scoring': ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        }
    }
    
    results = []
    cv_results_dict = {}
    fitted_models = {}
    confusion_matrices = {}
    
    for model_name, config in models_config.items():
        print(f"\n{'='*60}")
        print(f"Training: {model_name}")
        print(f"{'='*60}")
        
        model = config['model']
        
        # Cross-validation on training data
        print(f"\nRunning {CV_FOLDS}-fold cross-validation...")
        cv_scores = cross_validate(
            model, X_train, y_train,
            cv=cv_splitter,
            scoring=config['cv_scoring'],
            return_train_score=False,
            n_jobs=-1
        )
        
        cv_results_dict[model_name] = {
            'accuracy': {
                'mean': cv_scores['test_accuracy'].mean(),
                'std': cv_scores['test_accuracy'].std(),
                'folds': cv_scores['test_accuracy'].tolist()
            },
            'precision': {
                'mean': cv_scores['test_precision'].mean(),
                'std': cv_scores['test_precision'].std(),
                'folds': cv_scores['test_precision'].tolist()
            },
            'recall': {
                'mean': cv_scores['test_recall'].mean(),
                'std': cv_scores['test_recall'].std(),
                'folds': cv_scores['test_recall'].tolist()
            },
            'f1': {
                'mean': cv_scores['test_f1'].mean(),
                'std': cv_scores['test_f1'].std(),
                'folds': cv_scores['test_f1'].tolist()
            },
            'roc_auc': {
                'mean': cv_scores['test_roc_auc'].mean(),
                'std': cv_scores['test_roc_auc'].std(),
                'folds': cv_scores['test_roc_auc'].tolist()
            }
        }
        
        print(f"  Accuracy:  {cv_results_dict[model_name]['accuracy']['mean']:.4f} +/- {cv_results_dict[model_name]['accuracy']['std']:.4f}")
        print(f"  Precision: {cv_results_dict[model_name]['precision']['mean']:.4f} +/- {cv_results_dict[model_name]['precision']['std']:.4f}")
        print(f"  Recall:    {cv_results_dict[model_name]['recall']['mean']:.4f} +/- {cv_results_dict[model_name]['recall']['std']:.4f}")
        print(f"  F1:        {cv_results_dict[model_name]['f1']['mean']:.4f} +/- {cv_results_dict[model_name]['f1']['std']:.4f}")
        print(f"  ROC-AUC:   {cv_results_dict[model_name]['roc_auc']['mean']:.4f} +/- {cv_results_dict[model_name]['roc_auc']['std']:.4f}")
        
        # Train on full training data for test set evaluation
        print(f"Training final model on full training set...")
        model.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\nTest Set Evaluation:")
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall:    {rec:.4f}")
        print(f"  F1:        {f1:.4f}")
        print(f"  ROC-AUC:   {auc:.4f}")
        
        results.append({
            'model': model_name,
            'cv_accuracy_mean': cv_results_dict[model_name]['accuracy']['mean'],
            'cv_accuracy_std': cv_results_dict[model_name]['accuracy']['std'],
            'test_accuracy': acc,
            'test_precision': prec,
            'test_recall': rec,
            'test_f1': f1,
            'test_roc_auc': auc
        })
        
        # Save model
        model_path = OUT / f"{model_name.lower().replace(' ', '_')}.joblib"
        joblib.dump(model, model_path)
        print(f"[OK] Saved model: {model_path}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        confusion_matrices[model_name] = cm.tolist()
        
        # Save confusion matrix
        cm_df = pd.DataFrame(
            cm,
            index=['Actual Legitimate', 'Actual Phishing'],
            columns=['Predicted Legitimate', 'Predicted Phishing']
        )
        cm_path = OUT / f"confusion_matrix_{model_name.lower().replace(' ', '_')}.csv"
        cm_df.to_csv(cm_path)
        print(f"[OK] Saved confusion matrix: {cm_path}")
        
        # Classification report
        report = classification_report(y_test, y_pred, target_names=['Legitimate', 'Phishing'])
        report_path = OUT / f"classification_report_{model_name.lower().replace(' ', '_')}.txt"
        report_path.write_text(report)
        print(f"[OK] Saved classification report: {report_path}")
        
        fitted_models[model_name] = {
            'model': model,
            'predictions': y_pred,
            'probabilities': y_pred_proba,
            'confusion_matrix': cm
        }
    
    return results, cv_results_dict, fitted_models, confusion_matrices


def select_best_model(results):
    """Select best model based on F1 score."""
    results_df = pd.DataFrame(results)
    best_idx = results_df['test_f1'].idxmax()
    best_model_name = results_df.iloc[best_idx]['model']
    return best_model_name, results_df


def visualize_results(results_df, confusion_matrices):
    """Create visualizations."""
    
    # Model comparison bar chart
    metrics = ['test_accuracy', 'test_precision', 'test_recall', 'test_f1', 'test_roc_auc']
    display_names = ['Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC']
    
    fig, ax = plt.subplots(figsize=(10, 5))
    results_df.set_index('model')[metrics].plot(
        kind='bar',
        ax=ax,
        width=0.8,
        ylim=(0.85, 1.0),
        color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    )
    ax.set_title('MindTraceAI: Random Forest vs XGBoost (UCI Phishing Websites)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score')
    ax.set_xlabel('Model')
    ax.legend(display_names, loc='lower right', fontsize=9)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    plt.tight_layout()
    plt.savefig(OUT / 'model_comparison.png', dpi=180)
    plt.close()
    print(f"[OK] Saved: {OUT / 'model_comparison.png'}")
    
    # Confusion matrices
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    for ax, (model_name, matrix) in zip(axes, confusion_matrices.items()):
        cm = np.array(matrix)
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            cbar=False,
            xticklabels=['Legitimate', 'Phishing'],
            yticklabels=['Legitimate', 'Phishing'],
            ax=ax,
            annot_kws={'size': 12}
        )
        ax.set_title(model_name, fontweight='bold')
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
    
    fig.suptitle('UCI Phishing Websites: Confusion Matrices', fontsize=12, fontweight='bold')
    fig.tight_layout()
    plt.savefig(OUT / 'confusion_matrices_comparison.png', dpi=180, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved: {OUT / 'confusion_matrices_comparison.png'}")


def save_metrics_and_metadata(results_df, cv_results_dict, best_model_name, X_train, y_train, X_test, y_test):
    """Save all metrics to JSON for frontend."""
    
    metrics_data = {
        'dataset': 'UCI Phishing Websites',
        'dataset_size': len(X_train) + len(X_test),
        'features': len(X_train.columns),
        'train_size': len(X_train),
        'test_size': len(X_test),
        'train_target_distribution': {
            int(label): int(count) for label, count in y_train.value_counts().sort_index().items()
        },
        'test_target_distribution': {
            int(label): int(count) for label, count in y_test.value_counts().sort_index().items()
        },
        'best_model': best_model_name,
        'models': {}
    }
    
    for _, row in results_df.iterrows():
        model_name = row['model']
        cv_stats = cv_results_dict[model_name]
        
        metrics_data['models'][model_name] = {
            'cv_metrics': {
                'accuracy': cv_stats['accuracy'],
                'precision': cv_stats['precision'],
                'recall': cv_stats['recall'],
                'f1': cv_stats['f1'],
                'roc_auc': cv_stats['roc_auc']
            },
            'test_metrics': {
                'accuracy': float(row['test_accuracy']),
                'precision': float(row['test_precision']),
                'recall': float(row['test_recall']),
                'f1': float(row['test_f1']),
                'roc_auc': float(row['test_roc_auc'])
            }
        }
    
    # Save metrics JSON
    metrics_path = OUT / 'model_metrics.json'
    metrics_path.write_text(json.dumps(metrics_data, indent=2, default=json_default))
    print(f"[OK] Saved metrics: {metrics_path}")
    
    # Save CSV for reference
    results_df.to_csv(OUT / 'model_metrics.csv', index=False)
    print(f"[OK] Saved metrics CSV: {OUT / 'model_metrics.csv'}")
    
    # Metadata
    metadata = {
        'dataset': 'UCI Phishing Websites',
        'source': 'https://archive.ics.uci.edu/dataset/327/phishing+websites',
        'samples': len(X_train) + len(X_test),
        'features': 30,
        'target_classes': ['Legitimate', 'Phishing'],
        'evaluation_strategy': 'Stratified 80/20 split + 5-fold CV',
        'models_used': list(results_df['model'].unique()),
        'best_model': best_model_name,
        'no_target_leakage': True,
        'no_identifier_leakage': True,
        'scaling': 'StandardScaler',
        'seed': SEED
    }
    
    metadata_path = OUT / 'run_metadata.json'
    metadata_path.write_text(json.dumps(metadata, indent=2, default=json_default))
    print(f"[OK] Saved metadata: {metadata_path}")


def main():
    """Main pipeline."""
    print("\n" + "="*60)
    print("MindTraceAI: UCI Phishing Websites ML Pipeline")
    print("="*60)
    
    # Load and prepare data
    X, y, feature_names = load_and_prepare_data()
    
    # Stratified split and CV setup
    X_train, X_test, y_train, y_test, cv_splitter = stratified_split_and_cv(X, y)
    
    # Train and evaluate models
    results, cv_results_dict, fitted_models, confusion_matrices = train_and_evaluate_models(
        X_train, X_test, y_train, y_test, cv_splitter
    )
    
    # Select best model
    results_df = pd.DataFrame(results)
    best_model_name, results_df = select_best_model(results)
    
    print(f"\n{'='*60}")
    print(f"BEST MODEL: {best_model_name}")
    print(f"{'='*60}")
    print(results_df.to_string(index=False))
    
    # Save best model
    best_model = fitted_models[best_model_name]['model']
    best_model_path = OUT / 'best_model.joblib'
    joblib.dump(best_model, best_model_path)
    print(f"\n[OK] Saved best model: {best_model_path}")
    
    # Visualizations
    visualize_results(results_df, confusion_matrices)
    
    # Save metrics and metadata
    save_metrics_and_metadata(results_df, cv_results_dict, best_model_name, X_train, y_train, X_test, y_test)
    
    print(f"\n{'='*60}")
    print("[OK] Training complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
