"""Retrospective policy scenarios, not causal estimates. Python standard library."""
import argparse, csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RETURN_COST=1150
CALL_COST=45
EFFECT=.35
THRESHOLD=CALL_COST/(EFFECT*RETURN_COST)

def evaluate(rows, selector, effect=EFFECT):
    chosen=[r for r in rows if selector(r)]
    returns=sum(int(r['returned']) for r in chosen)
    n=len(chosen); prevented=returns*effect; cost=n*CALL_COST
    return dict(orders=len(rows),selected=n,selected_pct=n/len(rows) if rows else 0,selected_returns=returns,precision=returns/n if n else 0,recall=returns/sum(int(r['returned']) for r in rows) if any(int(r['returned']) for r in rows) else 0,expected_returns_prevented=prevented,call_cost_inr=cost,avoided_return_cost_inr=prevented*RETURN_COST,net_savings_inr=prevented*RETURN_COST-cost,break_even_effect=cost/(returns*RETURN_COST) if returns else None)

def main(folder):
    rows=list(csv.DictReader((ROOT/'data/holdout_predictions.csv').open()))
    paths=list(folder.glob('*-customers.csv'))+list(folder.glob('customers.csv'))
    assert len(paths)==1
    customers={r['customer_id']:r for r in csv.DictReader(paths[0].open())}
    for r in rows: r['shield_snapshot']=customers[r['customer_id']]['shield_member']
    select=lambda r:float(r['score'])>=THRESHOLD and r.get('policy_eligible','1')=='1'
    result={'assumptions':{'return_cost':RETURN_COST,'completed_call_cost':CALL_COST,'call_effect':EFFECT,'risk_threshold':THRESHOLD,'all_selected_calls_completed':True,'incremental_hold_cancellation_rate':.12},'policies':{'ship_all':evaluate(rows,lambda r:False),'call_all':evaluate(rows,lambda r:True),'targeted_call':evaluate(rows,select)},'fixed_threshold_sensitivity':{str(e):evaluate(rows,select,e) for e in [0,.10,.20,.35,.50]},'raw_score_sensitivity':evaluate(rows,lambda r:float(r['raw_score'])>=THRESHOLD),'groups':{},'hold_sensitivity':[]}
    for field in ['shield_snapshot','sales_channel']:
        result['groups'][field]={v:evaluate([r for r in rows if r[field]==v],select) for v in sorted({r[field] for r in rows})}
    chosen=[r for r in rows if select(r)]; ret=sum(int(r['returned']) for r in chosen); n=len(chosen)
    # Stylized independent cancellation: 12% of held orders cancel, 88% remain.
    # Cancelled would-return orders avoid handling cost; only cancelled would-keep orders lose margin.
    # No evidence for cancellation independence, incremental rate, or prevention effectiveness.
    for effect in [0,.10,.35]:
        for margin in [300,600,1000,2000]:
            avoided=ret*(.12+.88*effect)*RETURN_COST
            lost=.12*(n-ret)*margin
            result['hold_sensitivity'].append({'prevention_among_non_cancelled':effect,'contribution_margin_inr':margin,'expected_cancellations':.12*n,'avoided_handling_inr':avoided,'lost_kept_order_margin_inr':lost,'net_before_hold_admin_and_lifetime_value_inr':avoided-lost})
    result['baseline_return_handling_inr']=sum(int(r['returned']) for r in rows)*RETURN_COST
    (ROOT/'reports/economics.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,required=True);main(p.parse_args().input_dir)
