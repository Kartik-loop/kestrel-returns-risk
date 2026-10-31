"""Export trusted local sklearn artifact to portable JSON; no refitting."""
import argparse, csv, hashlib, json
from pathlib import Path
import joblib
ROOT=Path(__file__).resolve().parents[1]
def main(folder):
    saved=joblib.load(ROOT/'models/evaluation_model.joblib')
    pre, model=saved['model'].steps[0][1],saved['model'].steps[1][1]
    assert model.__class__.__name__=='LogisticRegression'
    cat, num=pre.transformers_[0],pre.transformers_[1]
    paths=list(folder.glob('*-products.csv'))+list(folder.glob('products.csv')); assert len(paths)==1
    products=list(csv.DictReader(paths[0].open()))
    artifact={'version':'kestrel-eval-v1','categorical':dict(zip(cat[2],[v.tolist() for v in cat[1].categories_])),'numeric':num[2],'mean':num[1].mean_.tolist(),'scale':num[1].scale_.tolist(),'coefficients':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),'calibration_slope':float(saved['calibrator'].coef_[0,0]),'calibration_intercept':float(saved['calibrator'].intercept_[0]),'products':{p['sku']:p for p in products},'provenance':{'model_sha256':hashlib.sha256((ROOT/'models/evaluation_model.joblib').read_bytes()).hexdigest(),'training_end':'2025-09-30','calibration_end':'2026-02-28','holdout_end':'2026-06-30'}}
    (ROOT/'assets').mkdir(exist_ok=True)
    (ROOT/'assets/model.json').write_text(json.dumps(artifact,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,required=True);main(p.parse_args().input_dir)
