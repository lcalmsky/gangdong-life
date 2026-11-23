import json, os, re, sys, time, urllib.parse, urllib.request
DATA = sys.argv[1]; OUT = sys.argv[2]
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
norm = lambda t: re.sub(r'[\s·\-_()]+', '', t).lower()
def search(q):
    url = "https://m.search.naver.com/search.naver?where=m_local&query=" + urllib.parse.quote(q)
    html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=15).read().decode('utf-8', 'replace')
    out = []
    for m in re.finditer(r'"coordinate":\{"__typename":"Coordinate","x":"([\d.]+)","y":"([\d.]+)"', html):
        head = html[max(0, m.start()-6000):m.start()]
        k = list(re.finditer(r'"([A-Za-z]+):(\d+)":\{"__typename"', head))
        if not k: continue
        obj = head[k[-1].start():]
        name = re.search(r'"name":"([^"]*)"', obj); addr = re.search(r'"address":"([^"]*)"', obj); road = re.search(r'"roadAddress":"([^"]*)"', obj)
        cat = re.search(r'"category":"([^"]*)"', obj)
        if name: out.append({'id': k[-1].group(2), 'name': name.group(1), 'address': addr.group(1) if addr else '', 'road': road.group(1) if road else '',
                             'category': cat.group(1) if cat else '', 'lng': float(m.group(1)), 'lat': float(m.group(2))})
    seen=set(); uniq=[]
    for o in out:
        if o['id'] in seen: continue
        seen.add(o['id']); uniq.append(o)
    return uniq
results = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
for cid in ('restaurants', 'cafes'):
    c = json.load(open(f'{DATA}/{cid}.json', encoding='utf-8'))
    for p in c['places']:
        if p['region'] not in ('강동', ''): continue
        q = p.get('mapQuery') or (f"{p['name']} {p['area']}" if p['area'] else f"{p['name']} 강동구")
        if results.get(f"{cid}/{p['name']}", {}).get('query') == q: continue
        try: cands = search(q)
        except Exception as e: print('ERR', p['name'], e, file=sys.stderr); continue
        pick = None
        for o in cands:
            if '강동구' in o['address'] and (norm(p['name']) in norm(o['name']) or norm(o['name']) in norm(p['name'])):
                pick = o; break
        results[f"{cid}/{p['name']}"] = {'query': q, 'pick': pick, 'cands': cands[:5]}
        print(('OK ' if pick else '-- ') + f"{cid}/{p['name']} -> " + (f"{pick['name']} | {pick['address']}" if pick else ', '.join(o['name'] + '(' + o['address'][:12] + ')' for o in cands[:3])))
        time.sleep(1.2)
json.dump(results, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
