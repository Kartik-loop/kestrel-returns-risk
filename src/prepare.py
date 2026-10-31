"""Read-only source audit and deterministic dispatch feature preparation (stdlib only)."""
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(folder, name):
    matches = list(folder.glob('*-' + name + '.csv')) + list(folder.glob(name + '.csv'))
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one {name}.csv, found {len(matches)}')
    path = matches[0]
    return list(csv.DictReader(path.open())), {'filename': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def write(name, rows):
    with (ROOT / 'data' / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main(folder):
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'reports').mkdir(exist_ok=True)
    data, manifest = {}, {}
    for n in ['train','test_unlabelled','customers','products','sample_submission']:
        data[n], manifest[n] = read(folder, n)
    refs = {}
    for name, key in [('customers','customer_id'),('products','sku')]:
        refs[name] = {r[key]: r for r in data[name]}
        assert len(refs[name]) == len(data[name]), f'Duplicate reference key: {name}'
    assert not ({r['order_id'] for r in data['train']} & {r['order_id'] for r in data['test_unlabelled']}), 'Train/test overlap'
    assert [r['order_id'] for r in data['test_unlabelled']] == [r['order_id'] for r in data['sample_submission']], 'Submission mismatch'
    audit = {'source_manifest': manifest, 'checks': 'Reference keys unique; joins complete; no train/test order overlap; submission IDs and order match.'}
    for name in ['train','test_unlabelled']:
        raw = data[name]; groups = defaultdict(list)
        for r in raw: groups[r['order_id']].append(r)
        rows, duplicate_log = [], []
        for oid, copies in groups.items():
            assert all(all(r[k] == copies[0][k] for k in r if k != 'source') for r in copies), f'Conflicting duplicate {oid}'
            chosen = next((r for r in copies if r['source'] == 'crm'), copies[0])
            rows.append(chosen)
            if len(copies)>1: duplicate_log.append({'order_id':oid,'copies':len(copies),'kept_source':chosen['source']})
        stats = {'raw_rows':len(raw),'unique_orders':len(rows),'duplicates_removed':len(raw)-len(rows), 'missing':{k:sum(not r[k].strip() for r in rows) for k in rows[0]}, 'date_min':min(r['order_placed_at'] for r in rows),'date_max':max(r['order_placed_at'] for r in rows)}
        counts = Counter(); monthly = defaultdict(lambda: Counter()); features=[]; cleaned=[]; issues=[]
        for r in rows:
            c=refs['customers'][r['customer_id']]; p=refs['products'][r['sku']]
            dt=datetime.strptime(r['order_placed_at'],'%Y-%m-%d %H:%M'); month=dt.strftime('%Y-%m')
            qty=int(r['qty']); discount=float(r['discount_pct']); amount=float(r['order_value_inr']); price=float(p['list_price_inr'])
            prior=int(r['customer_prior_orders']); returns=int(r['customer_prior_returns'])
            assert qty>0 and 0<=discount<=100 and 0<=returns<=prior and amount>=0
            assert re.fullmatch(r'\d{6}', r['delivery_pincode'])
            if name=='train': assert r['returned'] in ('0','1')
            expected=round(price*qty*(1-discount/100),2)
            corrected = month=='2025-10' and abs(amount/100-expected)<=0.011
            value=round(amount/100,2) if corrected else amount
            assert abs(value-expected)<=0.011, f'Unexplained price mismatch: {r["order_id"]}'
            signup=(dt.date()-datetime.strptime(c['signup_date'],'%Y-%m-%d').date()).days
            age=(dt.date()-datetime.strptime(p['launch_date'],'%Y-%m-%d').date()).days
            flags={'amount_divided_by_100':corrected,'signup_after_order':signup<0,'launch_after_order':age<0,'default_pincode':r['delivery_pincode']=='000000','instruction_like_note':bool(re.search('automated|assistant|do not drop|validation accuracy',r['delivery_note'],re.I))}
            counts.update({k:int(v) for k,v in flags.items()})
            for k,v in flags.items():
                if v: issues.append({'order_id':r['order_id'],'issue':k})
            monthly[month]['orders']+=1
            monthly[month]['amount_corrections']+=int(corrected)
            if name=='train': monthly[month]['returns']+=int(r['returned'])
            clean=dict(r,order_value_raw=r['order_value_inr'],order_value_inr=value,**{k:int(v) for k,v in flags.items()}); cleaned.append(clean)
            f={'order_id':r['order_id'],'order_placed_at':r['order_placed_at'],'customer_id':r['customer_id'], 'sku':r['sku'],'sales_channel':r['sales_channel'],'payment_mode':r['payment_mode'],'discount_pct':discount,'qty':qty,'order_value_inr':value,'promised_delivery_days':int(r['promised_delivery_days']),'is_gift':int(r['is_gift']=='Y'),'customer_prior_orders':prior,'customer_prior_returns':returns,'prior_return_rate':returns/prior if prior else 0,'no_prior_orders':int(prior==0),'address_missing':int(flags['default_pincode']),'family':p['family'],'list_price_inr':price,'product_age_days':age if age>=0 else '', 'order_month':dt.month,'order_weekday':dt.weekday(),'order_hour':dt.hour}
            if name=='train': f['returned']=int(r['returned'])
            features.append(f)
        stats.update(flags=dict(counts),monthly=dict(monthly),service_events=dict(Counter(r['last_service_event_type'] for r in rows)), sources=dict(Counter(r['source'] for r in rows)))
        if name=='train': stats['returns']=sum(int(r['returned']) for r in rows); stats['return_rate']=stats['returns']/len(rows)
        audit[name]=stats
        write(name+'_clean.csv',cleaned); write(name+'_features.csv',features)
        if issues: write(name+'_issues.csv',issues)
        if duplicate_log: write(name+'_duplicates.csv',duplicate_log)
    (ROOT/'reports'/'audit.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps({k:{x:v for x,v in audit[k].items() if x not in ['monthly','missing']} for k in ['train','test_unlabelled']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--input-dir',type=Path,required=True)
    main(parser.parse_args().input_dir)
