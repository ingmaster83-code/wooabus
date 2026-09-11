# -*- coding: utf-8 -*-
"""
fetch_train.py - 국토교통부(TAGO) 열차정보 수집 (KTX/SRT/새마을/무궁화 등)

fetch_express_bus.py와 동일한 전략(시드: 주요역 전수매칭 / cron: 전체역 풀에서 매일 일부씩 확장
+ 기존 노선 매일 갱신)을 쓰되, 이 API는 역 목록을 얻으려면 먼저 시/도 코드별로
GetCtyAcctoTrainSttnList를 호출해야 함(고속버스처럼 전체역 한번에 조회하는 엔드포인트 없음).
응답 필드명도 소문자(depplacename, adultcharge 등)로 버스 API와 다름.

사용법:
  python scripts/fetch_train.py            # 시드 실행(주요 역 전수) + 일일 갱신
  python scripts/fetch_train.py --daily     # cron용
"""
import json
import os
import random
import sys
import time
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

SERVICE_KEY = os.environ.get(
    "DATA_GO_KR_SERVICE_KEY",
    "9490b1d34e92aa9e25b32a4cff1438fc7b9c71e5d332413916a391e867f61e86",
)

BASE = "http://apis.data.go.kr/1613000/TrainInfo"
TODAY = date.today().isoformat()
NEW_PROBE_BUDGET = 3000
REQUEST_DELAY = 0.25
MAX_WORKERS = 3

MAJOR_KEYWORDS = [
    "서울", "용산", "영등포", "청량리", "수서", "인천", "수원", "천안", "대전",
    "세종", "오송", "전주", "광주송정", "목포", "여수", "순천", "동대구", "대구",
    "포항", "경주", "부산", "울산", "창원", "진주", "강릉", "춘천", "원주", "청주",
]


def get(op, params, attempt=1):
    p = dict(params)
    p["serviceKey"] = SERVICE_KEY
    p["_type"] = "json"
    try:
        r = requests.get(f"{BASE}/{op}", params=p, timeout=15)
        if r.status_code == 429:
            if attempt >= 6:
                print(f"  [실패-429] {op} {params}")
                return []
            time.sleep(4 * attempt)
            return get(op, params, attempt + 1)
        r.raise_for_status()
        data = r.json()
        body = data.get("response", {}).get("body", {})
        items = body.get("items")
        if not items:
            return []
        item = items.get("item", [])
        if isinstance(item, dict):
            item = [item]
        return item
    except Exception as e:
        if attempt >= 3:
            print(f"  [실패] {op} {params}: {e}")
            return []
        time.sleep(2 * attempt)
        return get(op, params, attempt + 1)


def fetch_all_stations():
    cities = get("GetCtyCodeList", {})
    print(f"  시/도 코드 {len(cities)}개")
    stations = []
    seen = set()
    for c in cities:
        items = get("GetCtyAcctoTrainSttnList", {"cityCode": c["citycode"], "numOfRows": 200, "pageNo": 1})
        for it in items:
            nid = it.get("nodeid")
            if nid and nid not in seen:
                seen.add(nid)
                stations.append({"terminalId": nid, "terminalNm": it.get("nodename", ""), "cityName": c["cityname"]})
        time.sleep(0.15)
    return stations


def pick_major(stations):
    out, seen = [], set()
    for s in stations:
        if s["terminalId"] in seen:
            continue
        if any(kw in s["terminalNm"] for kw in MAJOR_KEYWORDS):
            seen.add(s["terminalId"])
            out.append(s)
    return out


def probe_route(dep_id, arr_id, dep_nm, arr_nm):
    time.sleep(REQUEST_DELAY)
    items = get("GetStrtpntAlocFndTrainInfo", {
        "depPlaceId": dep_id, "arrPlaceId": arr_id, "numOfRows": 200, "pageNo": 1,
    })
    if not items:
        return None
    trips = []
    for it in items:
        trips.append({
            "depTime": it.get("depplandtime", ""),
            "arrTime": it.get("arrplandtime", ""),
            "charge": it.get("adultcharge", ""),
            "grade": it.get("traingradename", ""),
            "trainNo": it.get("trainno", ""),
        })
    trips.sort(key=lambda x: x["depTime"])
    return {
        "depTerminalId": dep_id, "depTerminalNm": dep_nm,
        "arrTerminalId": arr_id, "arrTerminalNm": arr_nm,
        "trips": trips, "fetchedAt": TODAY,
    }


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    daily = "--daily" in sys.argv
    print("=== 기차(KTX/SRT/새마을/무궁화) ===")
    stations = fetch_all_stations()
    print(f"  전체 역 {len(stations)}개 수집")
    save_json(DATA_DIR / "train_terminals.json", stations)

    majors = pick_major(stations)
    print(f"  주요 역 {len(majors)}개 선정")

    routes = load_json(DATA_DIR / "train_routes.json", [])
    routes_by_key = {f"{r['depTerminalId']}|{r['arrTerminalId']}": r for r in routes}
    tested = load_json(DATA_DIR / "train_tested.json", {})

    # 1) 기존 발견 노선 매일 갱신(API가 "오늘" 기준 데이터만 줌)
    refresh_keys = list(routes_by_key.keys())
    print(f"  기존 발견 노선 {len(refresh_keys)}개 갱신 시작")

    def _refresh(key):
        dep_id, arr_id = key.split("|")
        old = routes_by_key[key]
        res = probe_route(dep_id, arr_id, old["depTerminalNm"], old["arrTerminalNm"])
        return key, res

    refreshed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(_refresh, k) for k in refresh_keys]
        for i, fut in enumerate(as_completed(futs), 1):
            key, res = fut.result()
            if res:
                routes_by_key[key] = res
                refreshed += 1
            else:
                routes_by_key[key]["trips"] = []
                routes_by_key[key]["fetchedAt"] = TODAY
            if i % 500 == 0:
                print(f"    갱신 진행 {i}/{len(refresh_keys)}")
    print(f"  갱신 완료 (정상 {refreshed}건)")

    # 2) 신규 조합 탐색
    if daily:
        pending_pool = stations
        budget = NEW_PROBE_BUDGET
        stale_after_days = 30
    else:
        pending_pool = majors
        budget = 10 ** 9
        stale_after_days = None

    def _is_skippable(key):
        if key not in tested:
            return False
        if stale_after_days is None:
            return tested[key].get("date") == TODAY
        try:
            from datetime import date as _date
            age = (_date.today() - _date.fromisoformat(tested[key]["date"])).days
            return age < stale_after_days
        except Exception:
            return True

    candidates = []
    for a in pending_pool:
        for b in pending_pool:
            if a["terminalId"] == b["terminalId"]:
                continue
            key = f"{a['terminalId']}|{b['terminalId']}"
            if key in routes_by_key or _is_skippable(key):
                continue
            candidates.append((key, a, b))
    print(f"  미탐색 조합 {len(candidates)}개 중 최대 {budget}개 탐색")
    if daily:
        random.shuffle(candidates)
    candidates = candidates[:budget]

    def _probe(item):
        key, a, b = item
        res = probe_route(a["terminalId"], b["terminalId"], a["terminalNm"], b["terminalNm"])
        return key, res

    found_new = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(_probe, c) for c in candidates]
        for i, fut in enumerate(as_completed(futs), 1):
            key, res = fut.result()
            tested[key] = {"date": TODAY}
            if res:
                routes_by_key[key] = res
                found_new += 1
            if i % 500 == 0:
                print(f"    탐색 진행 {i}/{len(candidates)} (신규발견 {found_new})")
    print(f"  신규 발견 노선 {found_new}건")

    save_json(DATA_DIR / "train_routes.json", list(routes_by_key.values()))
    save_json(DATA_DIR / "train_tested.json", tested)
    print(f"  저장 완료: 총 {len(routes_by_key)}개 노선 -> train_routes.json")


if __name__ == "__main__":
    main()
