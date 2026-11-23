import json, math, sys
from shapely.geometry import shape, LineString, Polygon, box, mapping
from shapely.ops import polygonize, unary_union, linemerge
from shapely.validation import make_valid
S = sys.argv[1]
LNG0, LAT0, LNG1, LAT1 = 127.085, 37.59, 127.195, 37.505
K = math.cos(math.radians(37.545)); SC = 10000
X = lambda lng: (lng - LNG0) * K * SC
Y = lambda lat: (LAT0 - lat) * SC
W, H = round(X(LNG1)), round(Y(LAT1))
clip = box(LNG0, LAT1, LNG1, LAT0)
def pts(coords): return ' '.join(f'{X(x):.1f},{Y(y):.1f}' for x, y in coords)
def path(g, closed):
    out = []
    if g.is_empty: return ''
    geoms = getattr(g, 'geoms', [g])
    for p in geoms:
        if p.geom_type == 'Polygon':
            for ring in [p.exterior, *p.interiors]: out.append('M' + pts(ring.coords) + 'Z')
        elif p.geom_type == 'LineString': out.append('M' + pts(p.coords))
        elif p.geom_type in ('MultiPolygon', 'MultiLineString', 'GeometryCollection'): out.append(path(p, closed))
    return ''.join(out)
els = json.load(open(f'{S}/osm/raw.json'))['elements']
def way_line(e): return [(p['lon'], p['lat']) for p in e.get('geometry', [])]
def area_of(e):
    if e['type'] == 'way':
        c = way_line(e)
        return make_valid(Polygon(c)) if len(c) >= 4 else None
    lines = [LineString(way_line(m)) for m in e.get('members', []) if m.get('geometry') and m.get('role') in ('outer', '')]
    inner = [LineString(way_line(m)) for m in e.get('members', []) if m.get('geometry') and m.get('role') == 'inner']
    o = unary_union(list(polygonize(linemerge(lines)))) if lines else None
    if o is None: return None
    if inner:
        i = unary_union(list(polygonize(linemerge(inner))))
        o = o.difference(i)
    return make_valid(o)
water, green, roads = [], [], {'motorway': [], 'trunk': [], 'primary': [], 'secondary': []}
stations = []
for e in els:
    t = e.get('tags', {})
    if e['type'] == 'node':
        if t.get('name') and ('subway' in (t.get('station', '') + t.get('subway', '') + t.get('railway', '')) or t.get('railway') == 'station'):
            stations.append({'n': t['name'], 'x': round(X(e['lon']), 1), 'y': round(Y(e['lat']), 1)})
        continue
    if t.get('highway') in roads:
        c = way_line(e)
        if len(c) > 1: roads[t['highway']].append(LineString(c))
    elif t.get('natural') == 'water' or t.get('waterway') == 'riverbank':
        a = area_of(e); a and water.append(a)
    elif t.get('leisure') == 'park' or t.get('landuse') == 'forest':
        a = area_of(e)
        if a and a.area > 2e-6: green.append(a)
tol = 0.00003
water_g = unary_union(water).intersection(clip).simplify(tol)
green_g = unary_union(green).intersection(clip).difference(water_g).simplify(tol)
road_p = {k: path(unary_union(v).intersection(clip).simplify(tol), False) for k, v in roads.items()}
seoul = json.load(open(f'{S}/geo/seoul_dong.json'))['features']
gd = {f['properties']['EMD_KOR_NM']: make_valid(shape(f['geometry'])) for f in seoul if f['properties']['EMD_CD'].startswith('11740')}
gd_union = unary_union(list(gd.values()))
gd_out = gd_union.simplify(tol)
dong_lines = unary_union([g.boundary for g in gd.values()]).difference(gd_union.boundary.buffer(0.0002)).simplify(tol)
dongs = []
for n, g in gd.items():
    land = g.difference(water_g)
    p = land.representative_point() if land.area else g.representative_point()
    c = land.centroid
    if land.contains(c): p = c
    dongs.append({'n': n, 'x': round(X(p.x), 1), 'y': round(Y(p.y), 1)})
mask = clip.difference(gd_union).simplify(tol)
geo = json.load(open(f'{S}/geo-results.json', encoding='utf-8'))
places = []
for k, v in geo.items():
    if not v['pick']: continue
    cid, name = k.split('/', 1)
    p = v['pick']
    places.append({'c': cid, 'name': name, 'addr': p['road'] or p['address'], 'cat': p['category'], 'x': round(X(p['lng']), 1), 'y': round(Y(p['lat']), 1), 'lat': p['lat'], 'lng': p['lng']})
out = {'w': W, 'h': H, 'water': path(water_g, True), 'green': path(green_g, True), 'roads': road_p,
       'gangdong': path(gd_out, True), 'mask': path(mask, True), 'dongLines': path(dong_lines, False),
       'dongs': dongs, 'stations': stations, 'places': places}
open(sys.argv[2], 'w', encoding='utf-8').write('const MAP = ' + json.dumps(out, ensure_ascii=False) + ';\n')
print(W, H, len(places), len(stations), {k: len(v) for k, v in out.items() if isinstance(v, str)})
