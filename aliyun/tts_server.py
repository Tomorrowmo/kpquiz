#!/usr/bin/env python3
# 知识点闯关 · 朗读服务（微软 Edge 神经语音，本机缓存）
#   GET /tts?v=zh|en&t=<文本>[&r=-5%]  ->  audio/mpeg
#   GET /tts/health                      ->  ok
# 缓存目录 /var/cache/kptts，文件名 = sha1(voice|rate|text).mp3
import asyncio, hashlib, os, sys, urllib.parse, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import edge_tts

VOICES = {
    'zh': 'zh-CN-XiaoxiaoNeural',   # 温和、自然
    'zhy': 'zh-CN-XiaoyiNeural',    # 活泼，偏卡通
    'en': 'en-US-JennyNeural',      # 清楚、友好
    'kid': 'en-US-AnaNeural',       # 儿童音
}
RATE = {'zh': '-6%', 'zhy': '-4%', 'en': '-10%', 'kid': '-5%'}
CACHE = '/var/cache/kptts'
os.makedirs(CACHE, exist_ok=True)
LOCK = threading.Lock()
INFLIGHT = {}

def synth(text, voice, rate, path):
    async def run():
        tmp = path + '.part'
        await edge_tts.Communicate(text, voice, rate=rate).save(tmp)
        os.replace(tmp, path)
    asyncio.run(run())

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % a))
    def send(self, code, body=b'', ctype='text/plain; charset=utf-8', extra=None):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(body)
    def do_HEAD(self): self.do_GET()
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path.rstrip('/').endswith('/health'):
            return self.send(200, b'ok')
        q = urllib.parse.parse_qs(u.query)
        text = (q.get('t') or [''])[0].strip()
        v = (q.get('v') or ['zh'])[0]
        if v not in VOICES: v = 'zh'
        rate = (q.get('r') or [RATE[v]])[0]
        if not text: return self.send(400, b'empty')
        if len(text) > 800: text = text[:800]
        key = hashlib.sha1(('%s|%s|%s' % (VOICES[v], rate, text)).encode('utf-8')).hexdigest()
        path = os.path.join(CACHE, key + '.mp3')
        if not os.path.exists(path):
            with LOCK:
                ev = INFLIGHT.get(key)
                if ev is None:
                    ev = threading.Event(); INFLIGHT[key] = ev; owner = True
                else:
                    owner = False
            if owner:
                try:
                    synth(text, VOICES[v], rate, path)
                except Exception as e:
                    sys.stderr.write('synth failed: %r\n' % (e,))
                finally:
                    with LOCK: INFLIGHT.pop(key, None)
                    ev.set()
            else:
                ev.wait(40)
        if not os.path.exists(path):
            return self.send(502, b'tts failed')
        with open(path, 'rb') as f: data = f.read()
        self.send(200, data, 'audio/mpeg', {'Cache-Control': 'public, max-age=2592000', 'X-TTS-Voice': VOICES[v]})

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9011
    srv = ThreadingHTTPServer(('127.0.0.1', port), H)
    sys.stderr.write('kptts on 127.0.0.1:%d\n' % port)
    srv.serve_forever()
