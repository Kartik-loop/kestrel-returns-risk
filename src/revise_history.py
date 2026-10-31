"""History investigation: chronological development only for selection; exposed holdout is diagnostic."""
import json,sys,math
from pathlib import Path
import pandas as pd,numpy as np,joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,brier_score_loss,roc_auc_score,average_precision_score
from train import FEATURES,CAT
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import make_pipeline
ROOT=Path(__file__).resolve().parents[1]
HISTORY=['customer_prior_orders','customer_prior_returns','prior_return_rate','no_prior_orders']
BASE=[x for x in FEATURES if x not in HISTORY]
VARIANTS={'original':HISTORY,'counts_only':['customer_prior_orders','customer_prior_returns'],'rate_only':['prior_return_rate','no_prior_orders'],'smoothed_rate':['smoothed_return_rate','no_prior_orders'],'smoothed_success':['smoothed_return_rate','log_successful_orders','no_prior_orders']}
FOLDS=[('2025-07-01','2025-08-01','2025-09-01'),('2025-09-01','2025-10-01','2025-11-01'),('2025-11-01','2025-12-01','2026-01-01'),('2026-01-01','2026-02-01','2026-03-01')]
def derived(d,prior):
    d=d.copy();d['smoothed_return_rate']=(d.customer_prior_returns+5*prior)/(d.customer_prior_orders+5);d['log_successful_orders']=np.log1p(d.customer_prior_orders-d.customer_prior_returns);return d
def fit(d,kind):
    prior=float(d.returned.mean());d=derived(d,prior);features=BASE+VARIANTS[kind];num=[x for x in features if x not in CAT]
    pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT),('numeric',StandardScaler(),num)])
    model=make_pipeline(pre,LogisticRegression(C=1,max_iter=2000));model.fit(d[features],d.returned);return model,features,prior
def metrics(y,p):return {'n':len(y),'log_loss':log_loss(y,p),'brier':brier_score_loss(y,p),'auc':roc_auc_score(y,p),'average_precision':average_precision_score(y,p)}
def main():
    (ROOT/'models').mkdir(exist_ok=True)
    d=pd.read_csv(ROOT/'data/train_features.csv'); dates=d.order_placed_at
    plan={'variants':VARIANTS,'folds':FOLDS,'smoothing_strength':5,'selection':'Lowest pooled development log loss. No holdout selection. Raw probabilities fixed for all candidates; no calibration refit.','holdout_status':'April-June already exposed; diagnostic only.'}
    (ROOT/'reports/history_revision_plan.json').write_text(json.dumps(plan,indent=2))
    # Summaries never use final holdout labels for diagnosis or selection.
    dev=d[dates<'2026-03-01'].copy();dev['history_band']=pd.cut(dev.customer_prior_orders,[-1,0,2,5,9,100000])
    dev.groupby('history_band',observed=False).agg(orders=('returned','size'),return_rate=('returned','mean'),mean_prior_rate=('prior_return_rate','mean')).to_csv(ROOT/'reports/history_patterns.csv')
    comparison={};pooled={}
    for kind in VARIANTS:
        ys=[];ps=[];scores=[]
        for end,start,stop in FOLDS:
            tr=d[dates<end];va=d[(dates>=start)&(dates<stop)];model,features,prior=fit(tr,kind);p=model.predict_proba(derived(va,prior)[features])[:,1];ys.extend(va.returned);ps.extend(p);scores.append(metrics(va.returned,p))
        comparison[kind]={'folds':scores,'pooled':metrics(ys,ps)}
    chosen=min(comparison,key=lambda k:comparison[k]['pooled']['log_loss'])
    tr=d[dates<'2026-03-01'];model,features,prior=fit(tr,chosen);pre,lr=model.steps[0][1],model.steps[1][1];cat,num=pre.transformers_[:2]
    old=json.loads((ROOT/'reports/v1/model.json').read_text())
    artifact={**old,'version':'kestrel-history-v2','history_variant':chosen,'smoothing_prior':prior,'smoothing_strength':5,'categorical':dict(zip(cat[2],[v.tolist() for v in cat[1].categories_])),'numeric':num[2],'mean':num[1].mean_.tolist(),'scale':num[1].scale_.tolist(),'coefficients':lr.coef_[0].tolist(),'intercept':float(lr.intercept_[0]),'calibration_slope':1.,'calibration_intercept':0.,'provenance':{'training_end':'2026-02-28','calibration':'none; raw probability','holdout_status':'exposed diagnostic only'},'input_ranges':{k:[float(tr[k].min()),float(tr[k].max())] for k in ['customer_prior_orders','customer_prior_returns','discount_pct','qty','order_value_inr','promised_delivery_days']}}
    (ROOT/'assets/model.json').write_text(json.dumps(artifact,indent=2))
    joblib.dump({'model':model,'features':features,'prior':prior},ROOT/'models/history_v2.joblib')
    h=d[dates>='2026-04-01'].copy();p=model.predict_proba(derived(h,prior)[features])[:,1];h['raw_score']=p;h['score']=p;h[['order_id','customer_id','order_placed_at','sales_channel','returned','raw_score','score']].to_csv(ROOT/'data/holdout_predictions.csv',index=False)
    eligible=np.ones(len(h),dtype=bool)
    for k,(lo,hi) in artifact['input_ranges'].items(): eligible &= h[k].between(lo,hi).to_numpy()
    h['policy_eligible']=eligible.astype(int)
    h[['order_id','customer_id','order_placed_at','sales_channel','returned','raw_score','score','policy_eligible']].to_csv(ROOT/'data/holdout_predictions.csv',index=False)
    result={'selected':chosen,'comparison':comparison,'exposed_holdout_diagnostic':metrics(h.returned,p),'manual_review_count':int(sum(~eligible)),'training_rows':len(tr),'ranges':artifact['input_ranges']}
    (ROOT/'reports/history_revision_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
