#!/usr/bin/env python3
# 把固定的讲解文本提前生成好：python3 warm_cache.py texts.json
import json, sys, urllib.request, urllib.parse, time
texts = json.load(open(sys.argv[1], encoding='utf-8'))
ok = fail = 0; t0 = time.time()
for i, (v, t) in enumerate(texts):
    url = 'http://127.0.0.1:9011/tts?' + urllib.parse.urlencode({'v': v, 't': t})
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            r.read(); ok += 1
    except Exception as e:
        fail += 1; sys.stderr.write('fail %s: %s\n' % (t[:30], e))
    if i % 50 == 0: sys.stderr.write('%d/%d ok=%d fail=%d %.0fs\n' % (i, len(texts), ok, fail, time.time() - t0))
print('done ok=%d fail=%d in %.0fs' % (ok, fail, time.time() - t0))
