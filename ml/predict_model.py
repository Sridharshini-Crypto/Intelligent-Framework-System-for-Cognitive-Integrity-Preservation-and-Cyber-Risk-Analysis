"""Make predictions using the best trained MindTraceAI model.

Uses UCI Phishing Websites dataset features (30 phishing indicators).
Example: Classify a URL based on phishing characteristics.

Usage:
  python predict_model.py --input test_urls.csv
  python predict_model.py --show-features
"""

from pathlib import Path
import argparse
import json
import joblib
import pandas as pd
import numpy as np
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / 'artifacts' / 'best_model.joblib'
METADATA_PATH = ROOT / 'artifacts' / 'run_metadata.json'

# UCI Phishing Websites dataset features (30 total)
UCI_FEATURES = [
    'having_IP_Address',
    'URL_length',
    'Shortening_service',
    'having_at_symbol',
    'double_slash_redirecting',
    'Prefix_suffix',
    'having_sub_domain',
    'SSLfinal_state',
    'Domain_registration_length',
    'Favicon',
    'port',
    'HTTPS_token',
    'Request_URL',
    'URL_of_Anchor',
    'Links_in_tags',
    'SFH',
    'Submitting_to_email',
    'Abnormality',
    'Redirect',
    'on_mouseover',
    'RightClick',
    'popup_window',
    'Iframe',
    'age_of_domain',
    'DNSQuery',
    'web_traffic',
    'Page_Rank',
    'Google_Index',
    'Links_pointing_to_page',
    'Statistical_report'
]

def show_features():
    """Display available UCI features."""
    print("\nUCI Phishing Websites - 30 Phishing Indicators")
    print("="*60)
    for i, feat in enumerate(UCI_FEATURES, 1):
        print(f"{i:2d}. {feat}")
    print("\nAll features are integer values (-1, 0, or 1)")
    print("Use in CSV with column headers matching feature names exactly.\n")

def predict_single_url(feature_values):
    """Predict phishing risk for a single URL."""
    
    # Load model
    if not MODEL_PATH.exists():
        print("❌ Model not found. Train first:")
        print("  python ml/fetch_uci_dataset.py")
        print("  python ml/train_model.py")
        sys.exit(1)
    
    model = joblib.load(MODEL_PATH)
    
    # Create feature dataframe
    X = pd.DataFrame([feature_values])
    
    # Ensure all features present
    missing = [f for f in UCI_FEATURES if f not in X.columns]
    if missing:
        print(f"❌ Missing features: {missing}")
        sys.exit(1)
    
    # Reorder to match training order
    X = X[UCI_FEATURES]
    
    # Make prediction
    pred_class = model.predict(X)[0]
    pred_proba = model.predict_proba(X)[0]
    
    legitimate_prob = pred_proba[0]
    phishing_prob = pred_proba[1]
    
    # Determine risk tier
    if phishing_prob < 0.30:
        risk_tier = 'LOW'
        emoji = '🟢'
    elif phishing_prob < 0.70:
        risk_tier = 'MEDIUM'
        emoji = '🟡'
    else:
        risk_tier = 'HIGH'
        emoji = '🔴'
    
    return {
        'class': 'Phishing' if pred_class == 1 else 'Legitimate',
        'phishing_probability': float(phishing_prob),
        'legitimate_probability': float(legitimate_prob),
        'risk_tier': risk_tier,
        'emoji': emoji
    }

def predict_batch(input_file):
    """Predict phishing risk for multiple URLs from CSV."""
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    # Load data
    df = pd.read_csv(input_file)
    
    # Load model
    model = joblib.load(MODEL_PATH)
    
    # Ensure all features present
    missing = [f for f in UCI_FEATURES if f not in df.columns]
    if missing:
        print(f"❌ Missing features in CSV: {missing}")
        sys.exit(1)
    
    # Reorder features
    X = df[UCI_FEATURES]
    
    # Make predictions
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # Create output dataframe
    results = pd.DataFrame({
        'URL_Index': range(len(df)),
        'Predicted_Class': ['Phishing' if p == 1 else 'Legitimate' for p in predictions],
        'Legitimate_Prob': probabilities[:, 0],
        'Phishing_Prob': probabilities[:, 1],
        'Risk_Tier': [
            'LOW' if p < 0.30 else ('MEDIUM' if p < 0.70 else 'HIGH')
            for p in probabilities[:, 1]
        ]
    })
    
    # Save results
    output_file = input_file.parent / f"{input_file.stem}_predictions.csv"
    results.to_csv(output_file, index=False)
    
    print(f"\n✓ Predictions saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Total URLs: {len(results)}")
    print(f"  Legitimate: {(results['Predicted_Class'] == 'Legitimate').sum()}")
    print(f"  Phishing: {(results['Predicted_Class'] == 'Phishing').sum()}")
    print(f"\nRisk Distribution:")
    print(f"  🟢 LOW: {(results['Risk_Tier'] == 'LOW').sum()}")
    print(f"  🟡 MEDIUM: {(results['Risk_Tier'] == 'MEDIUM').sum()}")
    print(f"  🔴 HIGH: {(results['Risk_Tier'] == 'HIGH').sum()}")
    
    # Show sample
    print(f"\nFirst 5 predictions:")
    print(results.head().to_string(index=False))

def main():
    parser = argparse.ArgumentParser(
        description='Predict phishing risk using best trained MindTraceAI model'
    )
    parser.add_argument('--input', type=str, help='CSV file with URLs/features')
    parser.add_argument('--show-features', action='store_true', help='Show available features')
    
    args = parser.parse_args()
    
    if args.show_features:
        show_features()
        return
    
    if args.input:
        input_file = Path(args.input)
        predict_batch(input_file)
    else:
        # Interactive single prediction
        print("\nMindTraceAI - Single URL Prediction")
        print("="*60)
        print("Enter UCI feature values (integer: -1, 0, or 1)")
        print("Type 'features' to see all 30 features")
        print("Type 'exit' to quit\n")
        
        feature_values = {}
        for feat in UCI_FEATURES:
            while True:
                try:
                    val = input(f"{feat}: ").strip()
                    if val.lower() == 'features':
                        show_features()
                        continue
                    elif val.lower() == 'exit':
                        return
                    feature_values[feat] = int(val)
                    break
                except ValueError:
                    print("  Invalid input. Enter -1, 0, or 1")
        
        # Make prediction
        result = predict_single_url(feature_values)
        
        print("\n" + "="*60)
        print("PREDICTION RESULT")
        print("="*60)
        print(f"Classification: {result['class']}")
        print(f"Legitimate Probability: {result['legitimate_probability']:.2%}")
        print(f"Phishing Probability: {result['phishing_probability']:.2%}")
        print(f"Risk Tier: {result['emoji']} {result['risk_tier']}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
