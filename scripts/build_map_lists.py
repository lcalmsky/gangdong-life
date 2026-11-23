"""data/<id>.json 과 tools/map-build/geo-results.json 으로 지도 화면 목록(map/*-data.js)을 다시 만든다."""
import json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 좌표 변환은 tools/map-build/build.py 의 지도 범위와 같아야 핀이 지도 위 제자리에 놓인다
LNG0, LAT0, SC = 127.085, 37.59, 10000
K = math.cos(math.radians(37.545))
FILES = {'restaurants': 'list-data.js', 'cafes': 'cafes-data.js'}
# 맛집 목록은 처음 만들 때부터 업종의 마지막 낱말만 보여 줬다("육류,고기요리" → "고기요리"). 카페는 전체를 보여 준다
CAT_LAST_WORD = {'restaurants'}


def main():
    geo = json.loads((ROOT / 'tools/map-build/geo-results.json').read_text(encoding='utf-8'))
    for cid, fname in FILES.items():
        col = json.loads((ROOT / f'data/{cid}.json').read_text(encoding='utf-8'))
        places = []
        for p in col['places']:
            row = {'name': p['name'], 'area': p['area'], 'region': p['region'], 'note': p['note'], 'm': p['mentions'], 'self': p['self']}
            pick = (geo.get(f"{cid}/{p['name']}") or {}).get('pick')
            if pick:
                row.update(x=round((pick['lng'] - LNG0) * K * SC, 1), y=round((LAT0 - pick['lat']) * SC, 1),
                           addr=pick['road'] or pick['address'],
                           cat=pick['category'].split(',')[-1] if cid in CAT_LAST_WORD else pick['category'])
            places.append(row)
        out = {'title': col['title'], 'places': places}
        (ROOT / 'map' / fname).write_text('const LIST = ' + json.dumps(out, ensure_ascii=False) + ';\n', encoding='utf-8')
        print(f"{cid}: {len(places)}곳, 지도 핀 {sum('x' in r for r in places)}곳")


if __name__ == '__main__':
    main()
