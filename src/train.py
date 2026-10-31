"""Frozen chronological experiment. Does not use unlabelled test orders."""
import json, hashlib, platform
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn, joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, log_loss, confusion_matrix

ROOT=Path(__file__).resolve().parents[1]
FEATURES=['sku','sales_channel','payment_mode','discount_pct','qty','order_value_inr','promised_delivery_days','is_gift','customer_prior_orders','customer_prior_returns','prior_return_rate','no_prior_orders','address_missing','family','list_price_inr','product_age_days','order_month','order_weekday','order_hour']
CAT=['sku','sales_channel','payment_mode','family']

def metrics(y,p):
    tn,fp,fn,tp=confusion_matrix(y,p>=.5,labels=[0,1]).ravel()
    return dict(n=len(y),returns=int(sum(y)),prevalence=float(np.mean(y)),mean_score=float(np.mean(p)),roc_auc=roc_auc_score(y,p),average_precision=average_precision_score(y,p),brier=brier_score_loss(y,p),log_loss=log_loss(y,p),accuracy=float((tn+tp)/len(y)),precision=float(tp/(tp+fp)) if tp+fp else 0.,recall=float(tp/(tp+fn)),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp))

def main():
    d=pd.read_csv(ROOT/'data/train_features.csv'); dates=d.order_placed_at
    masks={'fit':dates<'2025-10-01','select':(dates>='2025-11-01')&(dates<'2026-01-01'),'calibrate':(dates>='2026-02-01')&(dates<'2026-03-01'),'holdout':dates>='2026-04-01'}
    # October, January and March are whole-month maturity buffers. No random split.
    parts={k:d.loc[m].copy() for k,m in masks.items()}
    plan={'splits':{k:{'n':len(v),'start':v.order_placed_at.min(),'end':v.order_placed_at.max()} for k,v in parts.items()},'selection':'minimum selection-window log loss among fixed candidates; no holdout tuning','calibration':'fixed sigmoid on February only; evaluate raw and calibrated on holdout, do not switch based on holdout','maturity_assumption':'One-month buffers are provisional, not proof of complete label maturity.','features':FEATURES,'data_sha256':hashlib.sha256((ROOT/'data/train_features.csv').read_bytes()).hexdigest()}
    (ROOT/'reports/experiment_plan.json').write_text(json.dumps(plan,indent=2))
    fit=parts['fit']; val=parts['select']; cal=parts['calibrate']; hold=parts['holdout']
    numeric=[f for f in FEATURES if f not in CAT]
    def prep(): return ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT),('numeric',StandardScaler(),numeric)])
    candidates={'constant':DummyClassifier(strategy='prior'),'logistic':LogisticRegression(C=1,max_iter=2000),'boosted_shallow':HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=7,min_samples_leaf=40,l2_regularization=10,learning_rate=.05,early_stopping=False,random_state=42),'boosted_medium':HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=10,learning_rate=.05,early_stopping=False,random_state=42)}
    models={}; comparison={}
    for name,est in candidates.items():
        model=make_pipeline(prep(),est); model.fit(fit[FEATURES],fit.returned); models[name]=model
        comparison[name]=metrics(val.returned,model.predict_proba(val[FEATURES])[:,1])
    chosen=min(comparison,key=lambda n:comparison[n]['log_loss']); model=models[chosen]
    def logits(p):
        p=np.clip(p,1e-6,1-1e-6); return np.log(p/(1-p)).reshape(-1,1)
    calibrator=LogisticRegression(C=1e6,max_iter=2000).fit(logits(model.predict_proba(cal[FEATURES])[:,1]),cal.returned)
    raw=model.predict_proba(hold[FEATURES])[:,1]; scores=calibrator.predict_proba(logits(raw))[:,1]
    base=models['constant'].predict_proba(hold[FEATURES])[:,1]
    result={'selected':chosen,'selection_metrics':comparison,'holdout_raw':metrics(hold.returned,raw),'holdout_calibrated':metrics(hold.returned,scores),'holdout_constant':metrics(hold.returned,base),'calibration_slope':float(calibrator.coef_[0,0]),'calibration_intercept':float(calibrator.intercept_[0]),'versions':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__,'joblib':joblib.__version__}}
    h=hold[['order_id','customer_id','order_placed_at','sales_channel','returned']].copy(); h['raw_score']=raw; h['score']=scores
    h['seen_customer']=h.customer_id.isin(set(fit.customer_id)|set(val.customer_id)|set(cal.customer_id))
    h.to_csv(ROOT/'data/holdout_predictions.csv',index=False)
    result['subgroups']={}
    for field in ['sales_channel','seen_customer']:
        result['subgroups'][field]={str(k):metrics(g.returned,g.score.to_numpy()) for k,g in h.groupby(field) if g.returned.nunique()==2}
    result['monthly']={k:metrics(g.returned,g.score.to_numpy()) for k,g in h.groupby(h.order_placed_at.str[:7])}
    h['risk_bin']=pd.cut(h.score,[0,.05,.10,.15,.20,.30,.50,1],include_lowest=True)
    h.groupby('risk_bin',observed=False).agg(orders=('returned','size'),mean_score=('score','mean'),return_rate=('returned','mean')).to_csv(ROOT/'reports/calibration_bins.csv')
    # Customer-cluster bootstrap preserves dependence among repeat orders; conditional on fitted model.
    rng=np.random.default_rng(42); clusters=[g.index.to_numpy() for _,g in h.reset_index(drop=True).groupby('customer_id')]; y=hold.returned.to_numpy(); draws=[]
    for _ in range(500):
        ix=np.concatenate([clusters[i] for i in rng.integers(0,len(clusters),len(clusters))]); draws.append([roc_auc_score(y[ix],scores[ix]),average_precision_score(y[ix],scores[ix]),brier_score_loss(y[ix],scores[ix])])
    result['cluster_bootstrap_95pct']={k:np.quantile(np.array(draws)[:,i],[.025,.975]).tolist() for i,k in enumerate(['roc_auc','average_precision','brier'])}
    (ROOT/'reports/model_results.json').write_text(json.dumps(result,indent=2))
    (ROOT/'models').mkdir(exist_ok=True); joblib.dump({'model':model,'calibrator':calibrator,'features':FEATURES},ROOT/'models/evaluation_model.joblib')
    (ROOT/'requirements.txt').write_text('\n'.join(f'{"scikit-learn" if k=="sklearn" else k}=={v}' for k,v in result['versions'].items() if k!='python')+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
