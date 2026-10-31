"""Portable logistic inference and strict dispatch-time validation. No dependencies."""
import json, math, re
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
THRESHOLD=45/(.35*1150)
REQUIRED=['order_id','order_placed_at','sku','sales_channel','payment_mode','discount_pct','qty','order_value_inr','promised_delivery_days','is_gift','customer_prior_orders','customer_prior_returns','delivery_pincode']

class InputError(ValueError): pass

def sigmoid(x):
    return 1/(1+math.exp(-x)) if x>=0 else math.exp(x)/(1+math.exp(x))

class Scorer:
    def __init__(self,path=ROOT/'assets/model.json'):
        self.model=json.loads(Path(path).read_text())
        m=self.model
        assert len(m['coefficients'])==sum(len(v) for v in m['categorical'].values())+len(m['numeric'])

    def prepare(self,r):
        if not isinstance(r,dict): raise InputError('Send one order as a JSON object.')
        missing=[k for k in REQUIRED if k not in r or r[k] is None or r[k]=='']
        if missing: raise InputError('Missing required fields: '+', '.join(missing))
        if not isinstance(r['order_id'],str) or not 1<=len(r['order_id'])<=100: raise InputError('order_id must be text between 1 and 100 characters.')
        def number(k,lo,hi,integer=False):
            try:
                if isinstance(r[k],bool): raise ValueError()
                x=float(r[k])
            except (TypeError,ValueError): raise InputError(k+' must be a number.')
            if not math.isfinite(x) or not lo<=x<=hi or (integer and x!=int(x)): raise InputError(f'{k} must be {"a whole number " if integer else ""}between {lo} and {hi}.')
            return int(x) if integer else x
        try: dt=datetime.strptime(r['order_placed_at'],'%Y-%m-%d %H:%M')
        except (ValueError,TypeError): raise InputError('order_placed_at must be YYYY-MM-DD HH:MM in IST.')
        if not isinstance(r['sku'],str) or r['sku'] not in self.model['products']: raise InputError('Unknown SKU. Select a product from the supplied catalog.')
        p=self.model['products'][r['sku']]
        for k in ['sales_channel','payment_mode']:
            if r[k] not in self.model['categorical'][k]: raise InputError('Unsupported '+k+'.')
        if r['is_gift'] not in ['Y','N']: raise InputError('is_gift must be Y or N.')
        if not isinstance(r['delivery_pincode'],str) or not re.fullmatch(r'\d{6}',r['delivery_pincode']): raise InputError('delivery_pincode must be a six-digit string; use 000000 for missing.')
        qty=number('qty',1,1000,True); discount=number('discount_pct',0,100)
        amount=number('order_value_inr',0,1e10); prior=number('customer_prior_orders',0,1000000,True); returns=number('customer_prior_returns',0,1000000,True)
        days=number('promised_delivery_days',0,365,True)
        if returns>prior: raise InputError('Prior returns cannot exceed prior orders.')
        price=float(p['list_price_inr']); expected=round(price*qty*(1-discount/100),2); warnings=[]
        if dt.strftime('%Y-%m')=='2025-10' and abs(amount/100-expected)<=.011 and abs(amount-expected)>.011:
            amount=round(amount/100,2); warnings.append('Historical October 2025 amount converted from the verified 100× unit anomaly.')
        if abs(amount-expected)>.011: raise InputError('Order value does not reconcile with catalog price, quantity and discount. Check units or request a catalog review.')
        age=(dt.date()-datetime.strptime(p['launch_date'],'%Y-%m-%d').date()).days
        if age<0: raise InputError('Order date precedes product launch.')
        extras=sorted(set(r)-set(REQUIRED))
        if extras: warnings.append('Additional fields were ignored. Only documented dispatch inputs affect this score.')
        if dt.strftime('%Y-%m-%d')>'2026-06-30': warnings.append('This order is beyond the evaluated period. Performance on newer orders is unverified.')
        f={k:r[k] for k in ['sku','sales_channel','payment_mode']}
        f.update(discount_pct=discount,qty=qty,order_value_inr=amount,promised_delivery_days=days,is_gift=int(r['is_gift']=='Y'),customer_prior_orders=prior,customer_prior_returns=returns,prior_return_rate=returns/prior if prior else 0,no_prior_orders=int(prior==0),address_missing=int(r['delivery_pincode']=='000000'),family=p['family'],list_price_inr=price,product_age_days=age,order_month=dt.month,order_weekday=dt.weekday(),order_hour=dt.hour)
        f['smoothed_return_rate']=(returns+self.model.get('smoothing_strength',5)*self.model.get('smoothing_prior',.11))/(prior+self.model.get('smoothing_strength',5))
        f['log_successful_orders']=math.log1p(prior-returns)
        return f,warnings

    def infer(self,f):
        m=self.model; terms={}; i=0
        for field,categories in m['categorical'].items():
            terms[field]=0.
            for category in categories:
                terms[field]+=m['coefficients'][i]*int(f[field]==category); i+=1
        for j,field in enumerate(m['numeric']):
            terms[field]=m['coefficients'][i]*(float(f[field])-m['mean'][j])/m['scale'][j]; i+=1
        raw=sigmoid(m['intercept']+sum(terms.values())); clipped=min(max(raw,1e-6),1-1e-6)
        score=raw if m['calibration_slope']==1 and m['calibration_intercept']==0 else sigmoid(m['calibration_intercept']+m['calibration_slope']*math.log(clipped/(1-clipped)))
        return raw,score,terms

    def predict(self,r):
        f,warnings=self.prepare(r)
        outside=[k for k,(lo,hi) in self.model.get('input_ranges',{}).items() if not lo<=f[k]<=hi]
        limits=[]
        if outside:
            labels={'qty':'Quantity','customer_prior_orders':'Earlier orders','customer_prior_returns':'Earlier returns','discount_pct':'Discount (%)','order_value_inr':'Order value (₹)','promised_delivery_days':'Promised delivery days'}
            limits=[{'field':k,'label':labels.get(k,k),'value':f[k],'minimum':self.model['input_ranges'][k][0],'maximum':self.model['input_ranges'][k][1]} for k in outside]
            for x in limits:
                warnings.append(f"{x['label']}: entered {x['value']:g}; training data covers {x['minimum']:g}–{x['maximum']:g}. An estimate outside this range is unreliable.")
        if f['customer_prior_orders']>10:
            return {'review_reason':'Earlier orders exceed the configured manual-review limit of 10.','order_id':r['order_id'],'model_version':self.model['version'],'score':None,'raw_score':None,'recommendation':'manual_review','threshold':None,'expected_call_net_saving_inr':None,'reasons':[],'out_of_range_fields':outside,'unsupported_inputs':limits,'warnings':warnings,'status':'unsupported_input','action_executed':False,'policy_note':'No risk or savings estimate is available for this order. Review the details manually without an automatic hold. Do not change accurate inputs merely to obtain a score.'}
        raw,score,terms=self.infer(f)
        grouped={
          'purchase_history':(['customer_prior_orders','customer_prior_returns','prior_return_rate','no_prior_orders','smoothed_return_rate','log_successful_orders'],f"{f['customer_prior_returns']} returns across {f['customer_prior_orders']} earlier orders"),
          'product':(['sku','family','list_price_inr','product_age_days'],self.model['products'][f['sku']]['model_name']),
          'purchase_details':(['qty','discount_pct','order_value_inr','is_gift'],f"{f['qty']} item(s), {f['discount_pct']:g}% discount, ₹{f['order_value_inr']:,.2f}"),
          'channel_payment':(['sales_channel','payment_mode'],f"{f['sales_channel'].replace('_',' ')} order, {f['payment_mode'].replace('_',' ')} payment"),
          'delivery':(['address_missing','promised_delivery_days'],f"Delivery promised in {f['promised_delivery_days']} days; address {'missing' if f['address_missing'] else 'recorded'}"),
          'order_timing':(['order_month','order_weekday','order_hour'],'Order month, weekday and hour')}
        reasons=[]
        for group,(fields,label) in grouped.items():
            contribution=sum(terms.get(k,0) for k in fields)*self.model['calibration_slope']
            reasons.append({'factor':group,'detail':label,'direction':'raises' if contribution>0 else 'lowers','log_odds_contribution':contribution})
        reasons.sort(key=lambda x:abs(x['log_odds_contribution']),reverse=True)
        outside=[k for k,(lo,hi) in self.model.get('input_ranges',{}).items() if not lo<=f[k]<=hi]
        if outside: warnings.append('Provisional extrapolation: accuracy for these values has not been measured. No financial benefit estimate is provided.')
        return {'score_basis':'extrapolated' if outside else 'within_observed_ranges','unsupported_inputs':limits,'out_of_range_fields':outside,'order_id':r['order_id'],'model_version':self.model['version'],'score':score,'raw_score':raw,'recommendation':('confirmation_call' if score>=THRESHOLD else 'normal_dispatch'),'threshold':THRESHOLD,'expected_call_net_saving_inr':None if outside else score*.35*1150-45,'reasons':reasons[:3],'explanation_note':'These are model associations relative to its mathematical reference, not causes or percentage-point changes. Related inputs are grouped; the top three do not sum to the final probability.','warnings':warnings,'status':'provisional_extrapolation' if outside else 'pilot_only','action_executed':False,'policy_note':'Consider a helpful confirmation call within the dispatch promise. No automatic hold. Estimated benefit assumes 35% prevention, ₹1,150 handling cost and ₹45 per completed call.'}
