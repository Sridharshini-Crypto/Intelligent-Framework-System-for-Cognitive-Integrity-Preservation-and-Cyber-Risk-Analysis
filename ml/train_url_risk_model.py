"""MindTraceAI phishing-URL ML pipeline: RF + XGBoost + SVM.

Uses the verified binary `label` in the PhiUSIIL dataset. Low/Medium/High
tiers are derived from the best model's phishing probability; they are a
decision-support output, not a second ground-truth label.
"""
from pathlib import Path
import argparse, json, joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'PhiUSIIL_Phishing_URL_Dataset.csv'; OUT=ROOT/'artifacts'/'url_risk'; OUT.mkdir(parents=True,exist_ok=True); SEED=42

def prepare(frame):
    drop=['label','FILENAME','URL','Domain','Title']
    X=frame.drop(columns=[x for x in drop if x in frame],errors='ignore')
    # Keep compact categorical signals; all other columns in this dataset are numeric.
    categorical=X.select_dtypes(include=['object']).columns.tolist(); numeric=[x for x in X.columns if x not in categorical]
    return X,numeric,categorical

def tier(p): return 'Low' if p<.33 else ('Medium' if p<.66 else 'High')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sample',type=int,default=30000,help='stratified training sample, default 30000 for practical local training');parser.add_argument('--show',action='store_true');args=parser.parse_args()
    if not DATA.exists():raise SystemExit(f'Dataset not found: {DATA}')
    raw=pd.read_csv(DATA,low_memory=False); y=raw['label'].astype(int)
    if args.sample and len(raw)>args.sample:
        raw, _=train_test_split(raw,train_size=args.sample,stratify=y,random_state=SEED); y=raw['label'].astype(int)
    X,numeric,categorical=prepare(raw)
    # Strict domain-group holdout: URLs from the same domain are never allowed
    # in both training and test data. This prevents memorisation of domain-level
    # patterns and produces a more trustworthy than a random-row split.
    groups=raw['Domain'].fillna(raw['FILENAME']).astype(str)
    splitter=GroupShuffleSplit(n_splits=1,test_size=.20,random_state=SEED)
    train_idx,test_idx=next(splitter.split(X,y,groups=groups))
    Xtr,Xte=X.iloc[train_idx],X.iloc[test_idx]; ytr,yte=y.iloc[train_idx],y.iloc[test_idx]
    prep=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric),('cat',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('onehot',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical)])
    models={'Random Forest':RandomForestClassifier(n_estimators=300,min_samples_leaf=2,class_weight='balanced',n_jobs=-1,random_state=SEED),'XGBoost':XGBClassifier(n_estimators=220,max_depth=5,learning_rate=.06,subsample=.85,colsample_bytree=.85,eval_metric='logloss',n_jobs=-1,random_state=SEED),'SVM':SVC(C=2,kernel='rbf',probability=True,class_weight='balanced',random_state=SEED)}
    rows=[]; matrices={}; fitted={}
    for name,model in models.items():
        pipe=Pipeline([('preprocess',prep),('model',model)]);pipe.fit(Xtr,ytr);pred=pipe.predict(Xte);prob=pipe.predict_proba(Xte)[:,1];matrix=confusion_matrix(yte,pred);matrices[name]=matrix;fitted[name]=(pipe,prob)
        rows.append({'model':name,'accuracy':accuracy_score(yte,pred),'precision':precision_score(yte,pred),'recall':recall_score(yte,pred),'f1':f1_score(yte,pred),'roc_auc':roc_auc_score(yte,prob)})
        safe=name.lower().replace(' ','_');joblib.dump(pipe,OUT/f'{safe}.joblib');pd.DataFrame(matrix,index=['Actual legitimate','Actual phishing'],columns=['Predicted legitimate','Predicted phishing']).to_csv(OUT/f'confusion_matrix_{safe}.csv');(OUT/f'classification_report_{safe}.txt').write_text(classification_report(yte,pred,target_names=['Legitimate','Phishing']))
    results=pd.DataFrame(rows).sort_values('f1',ascending=False);results.to_csv(OUT/'model_metrics.csv',index=False);best=results.iloc[0]['model'];joblib.dump(fitted[best][0],OUT/'best_url_risk_model.joblib')
    ax=results.set_index('model')[['accuracy','precision','recall','f1','roc_auc']].plot.bar(figsize=(10,5),ylim=(0,1),colormap='viridis');ax.set_title('Phishing URL model comparison');ax.set_ylabel('Score');plt.xticks(rotation=0);plt.tight_layout();plt.savefig(OUT/'url_model_comparison.png',dpi=180);plt.close()
    fig,axes=plt.subplots(1,3,figsize=(15,4.5));
    for axis,(name,matrix) in zip(axes,matrices.items()):sns.heatmap(matrix,annot=True,fmt='d',cmap='YlGnBu',cbar=False,xticklabels=['Legitimate','Phishing'],yticklabels=['Legitimate','Phishing'],ax=axis);axis.set_title(name);axis.set_xlabel('Predicted');axis.set_ylabel('Actual')
    fig.suptitle('Phishing URL: confusion matrix comparison');fig.tight_layout();fig.savefig(OUT/'url_confusion_matrix_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
    probability=fitted[best][1];tiers=pd.Series([tier(p) for p in probability]).value_counts().reindex(['Low','Medium','High'],fill_value=0);tiers.to_csv(OUT/'risk_level_distribution.csv',header=['profiles']);tiers.plot.bar(color=['#4f9d69','#e0ad4d','#c76053'],figsize=(7,4),title='Predicted phishing risk level distribution');plt.ylabel('Test URLs');plt.tight_layout();plt.savefig(OUT/'risk_level_distribution.png',dpi=180);plt.close()
    print('Training complete. Best model:',best);print(results.to_string(index=False,float_format=lambda n:f'{n:.3f}'));print('\nConfusion matrices (rows=actual, columns=predicted; [Legitimate, Phishing])');
    for name,matrix in matrices.items():print(f'\n{name}\n{matrix}')
    print('\nRisk-level output from best-model phishing probability:');print(tiers.to_string());print(f'\nSaved graph: {OUT / "url_model_comparison.png"}');print(f'Saved confusion matrix: {OUT / "url_confusion_matrix_comparison.png"}');print(f'Saved risk-level graph: {OUT / "risk_level_distribution.png"}')
    (OUT/'run_metadata.json').write_text(json.dumps({'dataset':DATA.name,'target':'label','classes':{'0':'Legitimate','1':'Phishing'},'evaluation':'Domain-group holdout: a domain is present in train or test, never both','risk_tier_rule':'Low < 0.33, Medium 0.33-0.65, High >= 0.66 predicted phishing probability','best_model':best,'sample_size':len(raw),'train_rows':len(Xtr),'test_rows':len(Xte),'train_domains':int(groups.iloc[train_idx].nunique()),'test_domains':int(groups.iloc[test_idx].nunique())},indent=2))

if __name__=='__main__':main()
