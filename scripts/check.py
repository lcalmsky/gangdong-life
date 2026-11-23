#!/usr/bin/env python3
"""Validate data/*.json before committing. Exit 1 on any error."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REGIONS = {"", "강동", "송파", "하남"}
PLACE_KEYS = {"name": str, "area": str, "region": str, "note": str, "mentions": int, "self": bool}
errors = []


def err(msg):
    errors.append(msg)


site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
for k in ("title", "greeting", "collections"):
    if k not in site:
        err(f"site.json: '{k}' 없음")

kinds = set(re.findall(r"^\s{2}(\w+): `<svg", (ROOT / "assets/app.js").read_text(encoding="utf-8"), re.M))
listed = site.get("collections", [])
if len(listed) != len(set(listed)):
    err("site.json: collections 에 중복 id")
on_disk = {p.stem for p in DATA.glob("*.json")} - {"site"}
for orphan in sorted(on_disk - set(listed)):
    err(f"data/{orphan}.json 이 site.json collections 에 없음")

for cid in listed:
    path = DATA / f"{cid}.json"
    if not path.exists():
        err(f"{cid}: data/{cid}.json 없음")
        continue
    c = json.loads(path.read_text(encoding="utf-8"))
    tag = f"data/{cid}.json"
    if c.get("id") != cid:
        err(f"{tag}: id '{c.get('id')}' 가 파일 이름과 다름")
    for k in ("title", "summary", "kind", "updated", "places"):
        if not c.get(k):
            err(f"{tag}: '{k}' 비어 있음")
    if c.get("kind") and c["kind"] not in kinds:
        print(f"  참고 {tag}: kind '{c['kind']}' 그림이 app.js ILL 에 없어 place 그림으로 표시됨")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(c.get("updated", ""))):
        err(f"{tag}: updated 는 YYYY-MM-DD")
    seen = set()
    for i, p in enumerate(c.get("places", [])):
        where = f"{tag} places[{i}] {p.get('name', '?')}"
        for k, t in PLACE_KEYS.items():
            if not isinstance(p.get(k), t) or (t is int and isinstance(p.get(k), bool)):
                err(f"{where}: '{k}' 는 {t.__name__}")
        if p.get("region") not in REGIONS:
            err(f"{where}: region '{p.get('region')}' 는 {sorted(REGIONS)} 중 하나")
        if isinstance(p.get("mentions"), int) and p["mentions"] < 1:
            err(f"{where}: mentions 는 1 이상")
        key = re.sub(r"\s+", "", str(p.get("name", "")))
        if key in seen:
            err(f"{where}: 같은 모음 안에 이름 중복")
        seen.add(key)
        if p.get("area") and not p.get("region") and "mapQuery" not in p:
            print(f"  참고 {where}: area '{p['area']}' 가 있는데 region 이 비어 있음")
    print(f"{cid}: {len(c.get('places', []))}곳")

# 지도 화면은 data 가 아니라 map/*-data.js 를 읽는다. scripts/build_map_lists.py 를 다시 돌리지 않으면 여기서 걸린다
MAP_LISTS = {"restaurants": "list-data.js", "cafes": "cafes-data.js"}
for cid, fname in MAP_LISTS.items():
    js = ROOT / "map" / fname
    if not js.exists() or not (DATA / f"{cid}.json").exists():
        err(f"map/{fname} 또는 data/{cid}.json 없음")
        continue
    lst = json.loads(re.search(r"=\s*(\{.*\})\s*;?\s*$", js.read_text(encoding="utf-8"), re.S).group(1))
    col = json.loads((DATA / f"{cid}.json").read_text(encoding="utf-8"))
    want = [(p["name"], p["mentions"], p["area"], p["note"]) for p in col["places"]]
    have = [(p["name"], p["m"], p["area"], p["note"]) for p in lst["places"]]
    if want != have:
        err(f"map/{fname} 가 data/{cid}.json 과 다름. python3 scripts/build_map_lists.py 를 돌릴 것")
    geo = json.loads((ROOT / "tools/map-build/geo-results.json").read_text(encoding="utf-8"))
    picked = {p["name"] for p in col["places"] if (geo.get(f"{cid}/{p['name']}") or {}).get("pick")}
    if picked != {p["name"] for p in lst["places"] if "x" in p}:
        err(f"map/{fname} 의 핀이 geo-results.json 과 다름. python3 scripts/build_map_lists.py 를 돌릴 것")
    for p in lst["places"]:
        if "x" in p and not p.get("addr"):
            err(f"map/{fname} {p['name']}: 지도 핀이 있는데 addr 없음")
    print(f"map/{fname}: 지도 핀 {sum('x' in p for p in lst['places'])}곳 / {len(lst['places'])}곳")

if errors:
    print("\n오류 " + str(len(errors)) + "건")
    for e in errors:
        print(" - " + e)
    sys.exit(1)
print("OK")
