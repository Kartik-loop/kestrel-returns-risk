"""Generate submission using exactly the portable serving model. No dependencies."""
import argparse,csv,hashlib,json,math
from pathlib import Path
from scoring import Scorer,ROOT

def main(input_path,template):
    rows=list(csv.DictReader(input_path.open()));expected=list(csv.DictReader(template.open()))
    ids=[r['order_id'] for r in rows]
    if len(ids)!=len(set(ids)) or ids!=[r['order_id'] for r in expected]: raise ValueError('Duplicate IDs or template mismatch.')
    scorer=Scorer();out=[]
    for row in rows:
        result=scorer.predict(row);score=result['score']
        if score is None or not math.isfinite(score) or not 0<=score<=1: raise ValueError('Cannot submit this order: '+row['order_id'])
        out.append({'order_id':row['order_id'],'score':format(score,'.15g')})
    path=ROOT/'predictions.csv'
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['order_id','score']);w.writeheader();w.writerows(out)
    manifest={'model_version':scorer.model['version'],'orders':len(out),'columns':['order_id','score'],'model_sha256':hashlib.sha256((ROOT/'assets/model.json').read_bytes()).hexdigest(),'predictions_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),'template_sha256':hashlib.sha256(template.read_bytes()).hexdigest(),'manual_review_rule':'customer_prior_orders > 10; other valid out-of-range values scored provisionally','model_changed':False}
    (ROOT/'reports/release_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--template',type=Path,required=True);a=p.parse_args();main(a.input,a.template)
