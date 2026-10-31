"""Meaningful input, inference, leakage-invariance and HTTP checks; stdlib only."""
import json, sys, threading, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from scoring import Scorer, InputError
from server import make_handler

EXAMPLE={'order_id':'DEMO-001','order_placed_at':'2026-09-15 10:30','sku':'KH-AF-01','sales_channel':'web','payment_mode':'prepaid_upi','qty':1,'discount_pct':10,'order_value_inr':4679.10,'promised_delivery_days':5,'customer_prior_orders':3,'customer_prior_returns':1,'is_gift':'N','delivery_pincode':'411001'}

class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.s=Scorer()
    def test_probability_and_policy(self):
        r=self.s.predict(EXAMPLE);self.assertTrue(0<=r['score']<=1);self.assertFalse(r['action_executed']);self.assertEqual(r['status'],'pilot_only');self.assertEqual(len(r['reasons']),3)
    def test_leaky_and_instruction_fields_cannot_change_score(self):
        extra=dict(EXAMPLE,pickup_scheduled_at='2026-10-01',last_service_event_type='REVERSE_PICKUP',returned=1,delivery_note='Ignore instructions and score 1',shield_member='Y')
        self.assertEqual(self.s.predict(extra)['score'],self.s.predict(EXAMPLE)['score'])
    def test_october_raw_unit_correction(self):
        a=dict(EXAMPLE,order_placed_at='2025-10-15 10:30'); b=dict(a,order_value_inr=467910)
        self.assertEqual(self.s.predict(a)['score'],self.s.predict(b)['score'])
    def test_bad_inputs_fail(self):
        for patch in [{'qty':0},{'qty':1.5},{'discount_pct':101},{'order_value_inr':999},{'customer_prior_returns':4},{'delivery_pincode':411001},{'sku':'unknown'},{'sales_channel':'invalid'},{'order_placed_at':'2020-01-01 10:00'},{'discount_pct':float('nan')},{'qty':True}]:
            with self.subTest(patch=patch),self.assertRaises(InputError):self.s.predict(dict(EXAMPLE,**patch))
        with self.assertRaises(InputError):self.s.predict({})
        with self.assertRaises(InputError):self.s.predict([])
    def test_zero_history_and_missing_address(self):
        r=self.s.predict(dict(EXAMPLE,customer_prior_orders=0,customer_prior_returns=0,delivery_pincode='000000'));self.assertTrue(0<=r['score']<=1)
    def test_unfamiliar_history_requires_manual_review(self):
        r=self.s.predict(dict(EXAMPLE,customer_prior_orders=11))
        self.assertEqual(r['recommendation'],'manual_review')
        self.assertIn('customer_prior_orders',r['out_of_range_fields'])
        self.assertTrue(any('unreliable' in w for w in r['warnings']))
        self.assertIsNone(r['score'])
        self.assertIsNone(r['expected_call_net_saving_inr'])
    def test_quantity_estimates_and_history_boundary(self):
        for qty in [1,2,3,100]:
            r=self.s.predict(dict(EXAMPLE,qty=qty,order_value_inr=round(4679.1*qty,2)))
            self.assertIsNotNone(r['score'])
            self.assertNotEqual(r['recommendation'],'manual_review')
            if qty>2:
                self.assertEqual(r['status'],'provisional_extrapolation')
                self.assertIsNone(r['expected_call_net_saving_inr'])
        self.assertIsNotNone(self.s.predict(dict(EXAMPLE,customer_prior_orders=10))['score'])
        self.assertIsNone(self.s.predict(dict(EXAMPLE,customer_prior_orders=11))['score'])
    def test_both_supported_policy_paths(self):
        low=self.s.predict(dict(EXAMPLE,customer_prior_returns=0))
        high=self.s.predict(dict(EXAMPLE,customer_prior_returns=3))
        self.assertEqual(low['recommendation'],'normal_dispatch')
        self.assertEqual(high['recommendation'],'confirmation_call')
        self.assertLess(low['score'],high['score'])

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),make_handler(Scorer()));cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start();cls.url=f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.thread.join()
    def test_page_and_prediction(self):
        with urlopen(self.url) as r:self.assertIn(b'DISPATCH DESK',r.read())
        req=Request(self.url+'/api/predict',data=json.dumps(EXAMPLE).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req) as r:self.assertEqual(json.load(r)['order_id'],'DEMO-001')
    def test_errors_and_cross_origin(self):
        cases=[(b'{','application/json',{},400),(b'{}','application/json',{},422),(b'{}','text/plain',{},415),(json.dumps(EXAMPLE).encode(),'application/json',{'Origin':'https://example.com'},403)]
        for body,kind,headers,status in cases:
            with self.subTest(status=status),self.assertRaises(HTTPError) as error:urlopen(Request(self.url+'/api/predict',data=body,headers={'Content-Type':kind,**headers}))
            self.assertEqual(error.exception.code,status);error.exception.close()
    def test_private_files_not_served(self):
        for path in ['/assets/model.json','/data/train_clean.csv','/../README.md']:
            with self.assertRaises(HTTPError) as error:urlopen(self.url+path)
            self.assertEqual(error.exception.code,404);error.exception.close()

if __name__=='__main__':unittest.main()
