"""Local-only demo server. Run from any working directory with Python 3.10+."""
import argparse, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from scoring import Scorer, InputError, ROOT

def make_handler(scorer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass  # Do not log order records.
        def send(self,status,value,kind='application/json; charset=utf-8'):
            body=json.dumps(value,allow_nan=False).encode() if kind.startswith('application/json') else value
            self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; connect-src 'self'")
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            path=urlsplit(self.path).path
            if path=='/api/health': return self.send(200,{'ready':scorer is not None,'model_version':scorer.model['version'] if scorer else None})
            if path=='/api/catalog':
                if not scorer: return self.send(503,{'error':'Model unavailable. Restore assets/model.json and restart.'})
                return self.send(200,list(scorer.model['products'].values()))
            files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
            if path in files:
                name,kind=files[path]; return self.send(200,(ROOT/'web'/name).read_bytes(),kind)
            self.send(404,{'error':'Not found.'})
        def do_POST(self):
            if urlsplit(self.path).path!='/api/predict': return self.send(404,{'error':'Not found.'})
            if not scorer: return self.send(503,{'error':'Model unavailable. Restore assets/model.json and restart.'})
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://{self.headers.get("Host")}': return self.send(403,{'error':'Cross-origin requests are not accepted.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'Use Content-Type: application/json.'})
            try: length=int(self.headers.get('Content-Length','0'))
            except ValueError: return self.send(400,{'error':'Invalid request length.'})
            if not 0<length<=65536: return self.send(413,{'error':'Send one order smaller than 64 KB.'})
            try:
                self.connection.settimeout(10)
                record=json.loads(self.rfile.read(length),parse_constant=lambda v: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
                result=scorer.predict(record)
            except (json.JSONDecodeError,UnicodeDecodeError): return self.send(400,{'error':'Invalid JSON. Check commas, quotes and brackets.'})
            except InputError as e: return self.send(422,{'error':str(e)})
            except ValueError: return self.send(400,{'error':'JSON values must be finite numbers.'})
            except (TimeoutError,OSError): return self.send(408,{'error':'Request timed out.'})
            except Exception: return self.send(500,{'error':'Unable to score this order. Check the local model artifact.'})
            self.send(200,result)
    return Handler

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);args=p.parse_args()
    try: scorer=Scorer()
    except (OSError,ValueError,AssertionError,KeyError): scorer=None; print('Model unavailable; the screen will show a helpful error.',flush=True)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(scorer))
    print(f'Kestrel local demo: http://127.0.0.1:{server.server_port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
