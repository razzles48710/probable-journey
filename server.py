"""Local talking mirror: Python 3.10+, no required third-party packages."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).parent / 'web'
OLLAMA = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
SYSTEM = ('You are the enchanted mirror of the Beshara household. Speak like a wise, '
          'warm, theatrical storybook oracle. Be playful, kind, and family friendly. '
          'Answer in one to three short sentences unless asked for more. Never rank '
          'people by beauty. You have no camera, live information, or ability to '
          'control devices. Be honest about that. Do not claim to perform actions.')

def reply(messages):
    if not isinstance(messages, list) or not 1 <= len(messages) <= 20:
        raise ValueError('Send between 1 and 20 messages.')
    for m in messages:
        if not isinstance(m, dict) or m.get('role') not in ('user', 'assistant'):
            raise ValueError('Invalid message role.')
        if not isinstance(m.get('content'), str) or len(m['content']) > 4000:
            raise ValueError('Each message must be text under 4000 characters.')
    payload = {'model': MODEL, 'stream': False,
               'messages': [{'role': 'system', 'content': SYSTEM}] + messages,
               'options': {'num_predict': 220}}
    request = urllib.request.Request(OLLAMA + '/api/chat',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=120) as response:
        answer = json.load(response)['message']['content']
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError('The model returned an empty answer.')
    return answer

class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, mime='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        routes = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                  '/style.css': ('style.css', 'text/css')}
        route = routes.get(self.path.split('?')[0])
        if route:
            self.send(200, (ROOT / route[0]).read_bytes(), route[1])
        else:
            self.send(404, b'{}')

    def do_POST(self):
        # Only the local mirror page may submit requests; no cross-origin API.
        if self.headers.get('Origin') not in (None, 'http://' + self.headers.get('Host', '')):
            return self.send(403, b'{"error":"Origin rejected"}')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 100000:
                raise ValueError('Invalid request size.')
            body = json.loads(self.rfile.read(size))
            if self.path == '/api/chat':
                answer = reply(body.get('messages'))
                return self.send(200, json.dumps({'text': answer}).encode())
            if self.path == '/api/tts':
                text = body.get('text')
                if not isinstance(text, str) or not 0 < len(text) <= 6000:
                    raise ValueError('Invalid speech text.')
                model = os.getenv('PIPER_MODEL')
                if not model:
                    return self.send(503, b'{"error":"Piper is not configured"}')
                with tempfile.TemporaryDirectory() as directory:
                    output = str(Path(directory) / 'voice.wav')
                    subprocess.run([os.getenv('PIPER_BIN', 'piper'), '-m', model, '-f', output],
                                   input=text, text=True, check=True, timeout=60,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return self.send(200, Path(output).read_bytes(), 'audio/wav')
            self.send(404, b'{}')
        except (ValueError, TypeError, AttributeError):
            self.send(400, b'{"error":"Invalid request. Check message length and format."}')
        except Exception:
            self.send(502, b'{"error":"Mirror service unavailable. Check Ollama/model or Piper configuration in the terminal."}')

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    print(f'Mirror ready: http://localhost:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
