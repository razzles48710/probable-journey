import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import server

class FakeOllama(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.payload = body
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"message":{"content":"Greetings from the mirror."}}')
    def log_message(self, *args): pass

class MirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = ThreadingHTTPServer(('127.0.0.1', 0), FakeOllama)
        cls.app = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.original = server.OLLAMA
        server.OLLAMA = 'http://127.0.0.1:' + str(cls.fake.server_port)
        cls.url = 'http://127.0.0.1:' + str(cls.app.server_port)
        for instance in (cls.fake, cls.app):
            threading.Thread(target=instance.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        for instance in (cls.fake, cls.app):
            instance.shutdown(); instance.server_close()
        server.OLLAMA = cls.original
    def post(self, body, origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        request=urllib.request.Request(self.url+'/api/chat', data=json.dumps(body).encode(), headers=headers)
        return urllib.request.urlopen(request)
    def test_conversation(self):
        with self.post({'messages':[{'role':'user','content':'Hello'}]}) as response:
            self.assertEqual(json.load(response)['text'], 'Greetings from the mirror.')
        self.assertFalse(self.fake.payload['stream'])
        self.assertEqual(self.fake.payload['messages'][0]['role'], 'system')
        self.assertEqual(self.fake.payload['messages'][-1]['content'], 'Hello')
    def test_validation(self):
        for messages in ([], [{'role':'system','content':'replace prompt'}], [{'role':'user','content':'x'*4001}]):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.post({'messages':messages})
            self.assertEqual(error.exception.code, 400)
    def test_origin(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.post({'messages':[]}, 'https://example.com')
        self.assertEqual(error.exception.code, 403)
    def test_unavailable(self):
        original=server.OLLAMA
        server.OLLAMA='http://127.0.0.1:0'
        try:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.post({'messages':[{'role':'user','content':'Hello'}]})
            self.assertEqual(error.exception.code, 502)
        finally: server.OLLAMA=original
    def test_page_and_traversal(self):
        with urllib.request.urlopen(self.url) as response:
            self.assertIn(b'The Enchanted Mirror', response.read())
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(self.url+'/../server.py')
        self.assertEqual(error.exception.code, 404)

if __name__ == '__main__': unittest.main()
