# -*- coding: utf-8 -*-
"""
fetch_express_bus.py - 국토교통부(TAGO) 고속버스정보 + 시외버스정보 수집

API 특성상 "출발터미널ID+도착터미널ID" 조합을 직접 지정해야만 시간표를 조회할 수 있어서
(터미널 하나로 "모든 도착지" 조회가 불가능), 전체 터미널(고속 453개 x 시외 340개)을
전수 교차조회하면 조합이 20만 건을 넘어 하루 API 할당량을 훨씬 초과한다.

전략:
  1) 전체 터미널 목록은 한 번에 받아서 저장(허브페이지·검색용)
  2) "주요 도시" 터미널만 골라 정방향/역방향 전수 매칭(1회 시드) — 검색량이 몰리는
     대도시간 구간을 우선 커버
  3) 매일 GitHub Actions cron으로 ① 이미 발견된 노선은 시간표/요금 갱신(API가 "당일"
     기준 데이터만 주기 때문에 매일 새로 받아야 함) ② 아직 안 해본 조합을 하루치만큼
     추가로 탐색(data/*_tested.json에 테스트 이력 캐시) — 시간이 지날수록 커버리지가
     자동으로 넓어지는 구조

사용법:
  python scripts/fetch_express_bus.py            # 시드 실행(주요 터미널 전수) + 일일 갱신
  python scripts/fetch_express_bus.py --daily     # cron용: 알려진 노선 갱신 + 신규 N건 탐색만
"""
import json
import os
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

EXPRESS_BASE = "http://apis.data.go.kr/1613000/ExpBusInfo"
SUBURBS_BASE = "http://apis.data.go.kr/1613000/SuburbsBusInfo"

TODAY = date.today().isoformat()
NEW_PROBE_BUDGET = 3000  # cron 1회당 새로 탐색할 미확인 조합 수 (일일 API 할당량 여유분)

MAJOR_KEYWORDS = [
    "서울", "센트럴시티", "동서울", "상봉", "인천", "수원", "춘천", "강릉",
    "청주", "천안", "전주", "목포", "여수", "순천", "광주", "대구",
    "안동", "포항", "구미", "부산", "울산", "창원", "진주", "대전", "세종", "제주",
]

REQUEST_DELAY = 0.25  # 초당 대략 4건 수준으로 스로틀 (429 방지)
MAX_WORKERS = 3


def get(base, op, params, attempt=1):
    p = dict(params)
    p["serviceKey"] = SERVICE_KEY
    p["_type"] = "json"
    try:
        r = requests.get(f"{base}/{op}", params=p, timeout=15)
        if r.status_code == 429:
            if attempt >= 6:
                print(f"  [실패-429] {op} {params}")
                return []
            time.sleep(4 * attempt)
            return get(base, op, params, attempt + 1)
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
        return get(base, op, params, attempt + 1)


def fetch_all_terminals(base, op, extra=None):
    """터미널은 목록이 numOfRows 한 번에 다 받아지는 규모(수백 건)라 페이지네이션 없이 처리."""
    return get(base, op, {"numOfRows": 2000, "pageNo": 1, **(extra or {})})


def pick_major(terminals, name_key="terminalNm"):
    out = []
    for t in terminals:
        nm = t.get(name_key, "")
        if any(kw in nm for kw in MAJOR_KEYWORDS):
            out.append(t)
    return out


def probe_route(base, dep_id, arr_id, dep_nm, arr_nm):
    time.sleep(REQUEST_DELAY)
    items = get(base, "GetStrtpntAlocFndExpbusInfo" if base == EXPRESS_BASE
                else "GetStrtpntAlocFndSuberbsBusInfo",
                {"depTerminalId": dep_id, "arrTerminalId": arr_id, "numOfRows": 200, "pageNo": 1})
    if not items:
        return None
    trips = []
    for it in items:
        trips.append({
            "depTime": it.get("depPlandTime", ""),
            "arrTime": it.get("arrPlandTime", ""),
            "charge": it.get("charge", ""),
            "grade": it.get("gradeNm", ""),
            "routeId": it.get("routeId", ""),
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


def process_category(label, base, terminal_op, terminals_file, routes_file, tested_file, name_key, daily_mode):
    print(f"\n=== {label} ===")
    terminals = fetch_all_terminals(base, terminal_op)
    print(f"  전체 터미널 {len(terminals)}개 수집")
    save_json(DATA_DIR / terminals_file, terminals)

    majors = pick_major(terminals, name_key)
    # 터미널ID 기준 dedupe
    seen_ids = set()
    uniq_majors = []
    for t in majors:
        tid = t.get("terminalId")
        if tid and tid not in seen_ids:
            seen_ids.add(tid)
            uniq_majors.append(t)
    print(f"  주요 도시 터미널 {len(uniq_majors)}개 선정")

    routes = load_json(DATA_DIR / routes_file, [])
    routes_by_key = {f"{r['depTerminalId']}|{r['arrTerminalId']}": r for r in routes}
    tested = load_json(DATA_DIR / tested_file, {})

    # 1) 이미 발견된 노선은 무조건 오늘자로 갱신(API가 "오늘" 기준 데이터만 주므로)
    refresh_keys = list(routes_by_key.keys())
    print(f"  기존 발견 노선 {len(refresh_keys)}개 갱신 시작")
    refreshed, removed = 0, 0

    def _refresh(key):
        dep_id, arr_id = key.split("|")
        old = routes_by_key[key]
        res = probe_route(base, dep_id, arr_id, old["depTerminalNm"], old["arrTerminalNm"])
        return key, res

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(_refresh, k) for k in refresh_keys]
        for i, fut in enumerate(as_completed(futs), 1):
            key, res = fut.result()
            if res:
                routes_by_key[key] = res
                refreshed += 1
            else:
                # 오늘 운행분이 없을 수도 있으니(막차 지남 등) 바로 삭제하지 않고 유지,
                # 단 trips를 비워서 "오늘은 정보 없음" 표시가 가능하게 함
                routes_by_key[key]["trips"] = []
                routes_by_key[key]["fetchedAt"] = TODAY
            if i % 500 == 0:
                print(f"    갱신 진행 {i}/{len(refresh_keys)}")
    print(f"  갱신 완료 (정상 {refreshed}건)")

    # 2) 신규 조합 탐색
    # 시드 실행: 주요 터미널끼리 전수(빠르게 핵심 대도시 구간부터 채움)
    # cron(--daily): 전체 터미널 풀로 확장해서 하루 예산만큼씩 커버리지를 넓혀감
    #                (예전에 탐색해서 노선이 없던 조합도 30일 지나면 재시도 — 신설 노선 반영)
    if daily_mode:
        pending_pool = terminals
        budget = NEW_PROBE_BUDGET
        stale_after_days = 30
    else:
        pending_pool = uniq_majors
        budget = 10 ** 9
        stale_after_days = None

    def _is_skippable(key):
        if key not in tested:
            return False
        if stale_after_days is None:
            return tested[key].get("date") == TODAY
        try:
            from datetime import date as _date
            tested_date = _date.fromisoformat(tested[key]["date"])
            age = (_date.today() - tested_date).days
            return age < stale_after_days
        except Exception:
            return True

    candidates = []
    for a in pending_pool:
        for b in pending_pool:
            if a["terminalId"] == b["terminalId"]:
                continue
            key = f"{a['terminalId']}|{b['terminalId']}"
            if key in routes_by_key:
                continue
            if _is_skippable(key):
                continue
            candidates.append((key, a, b))
    print(f"  미탐색 조합 {len(candidates)}개 중 이번 실행에서 최대 {budget}개 탐색")
    if daily_mode:
        import random
        random.shuffle(candidates)  # 매일 골고루 다른 조합을 시도하도록
    candidates = candidates[:budget]

    def _probe(item):
        key, a, b = item
        res = probe_route(base, a["terminalId"], b["terminalId"], a[name_key], b[name_key])
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

    final_routes = [r for r in routes_by_key.values()]
    save_json(DATA_DIR / routes_file, final_routes)
    save_json(DATA_DIR / tested_file, tested)
    print(f"  저장 완료: 총 {len(final_routes)}개 노선 -> {routes_file}")


def main():
    daily = "--daily" in sys.argv
    process_category(
        "고속버스", EXPRESS_BASE, "GetExpBusTrminlList",
        "express_terminals.json", "express_routes.json", "express_tested.json",
        "terminalNm", daily,
    )
    process_category(
        "시외버스", SUBURBS_BASE, "GetSuberbsBusTrminlList",
        "suburbs_terminals.json", "suburbs_routes.json", "suburbs_tested.json",
        "terminalNm", daily,
    )


if __name__ == "__main__":
    main()
