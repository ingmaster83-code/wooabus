# -*- coding: utf-8 -*-
"""한국교통안전공단 버스 노선/시간표 CSV -> data/routes.json"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
ROUTES_CSV = ROOT / "data" / "raw_routes.csv"
SCHEDULE_CSV = ROOT / "data" / "raw_schedule.csv"
OUT_JSON = ROOT / "data" / "routes.json"

SIGUNGU_TO_SIDO = {
    # 강원특별자치도
    "태백시": "강원특별자치도", "홍천군": "강원특별자치도", "영월군": "강원특별자치도", "철원군": "강원특별자치도",
    # 충청북도
    "영동군": "충청북도", "진천군": "충청북도", "괴산군": "충청북도", "음성군": "충청북도", "단양군": "충청북도",
    # 충청남도
    "논산시": "충청남도", "부여군": "충청남도", "당진시": "충청남도",
    # 전북특별자치도
    "정읍시": "전북특별자치도", "김제시": "전북특별자치도", "진안군": "전북특별자치도", "무주군": "전북특별자치도",
    "장수군": "전북특별자치도", "임실군": "전북특별자치도", "순창군": "전북특별자치도", "고창군": "전북특별자치도",
    "부안군": "전북특별자치도",
    # 전라남도
    "구례군": "전라남도", "고흥군": "전라남도", "장흥군": "전라남도", "해남군": "전라남도", "영암군": "전라남도",
    "장성군": "전라남도", "완도군": "전라남도", "진도군": "전라남도", "신안군": "전라남도",
    # 경상북도
    "영주시": "경상북도", "상주시": "경상북도", "문경시": "경상북도", "의성군": "경상북도", "청도군": "경상북도",
    "고령군": "경상북도", "성주군": "경상북도", "칠곡군": "경상북도", "봉화군": "경상북도", "울진군": "경상북도",
    "울릉군": "경상북도",
    # 경상남도
    "통영시": "경상남도", "의령군": "경상남도", "함안군": "경상남도", "창녕군": "경상남도", "고성군": "경상남도",
    "남해군": "경상남도", "하동군": "경상남도", "산청군": "경상남도", "함양군": "경상남도", "거창군": "경상남도",
    "합천군": "경상남도",
}

DAY_TYPES = ["매일", "평일", "토요일", "공휴일"]


def load_routes():
    routes = {}
    with open(ROUTES_CSV, encoding="cp949", newline="") as f:
        for row in csv.DictReader(f):
            rid = row["노선 아이디"]
            routes[rid] = {
                "id": rid,
                "name": row["노선명"].strip(),
                "start": row["기점정류장"].strip(),
                "end": row["종점정류장"].strip(),
                "city": row["지자체명"].strip(),
            }
    return routes


def load_schedule():
    sched = defaultdict(dict)
    with open(SCHEDULE_CSV, encoding="cp949", newline="") as f:
        for row in csv.DictReader(f):
            rid = row["노선 아이디"]
            day = row["요일"].strip()
            if day not in DAY_TYPES:
                continue
            sched[rid][day] = {
                "trips": row["일일운행횟수"].strip(),
                "start_first": row["기점첫차출발시각"].strip(),
                "start_last": row["기점막차출발시각"].strip(),
                "end_first": row["종점첫차출발시각"].strip(),
                "end_last": row["종점막차출발시각"].strip(),
                "min_interval": row["최소배차간격"].strip(),
                "max_interval": row["최대배차간격"].strip(),
            }
    return sched


def main():
    routes = load_routes()
    print(f"노선정보 {len(routes)}건 로드")
    sched = load_schedule()
    print(f"시간표 {len(sched)}개 노선 로드")

    unmatched_city = set()
    by_city = defaultdict(list)
    joined = 0
    for rid, day_sched in sched.items():
        r = routes.get(rid)
        if not r:
            continue
        city = r["city"]
        if city not in SIGUNGU_TO_SIDO:
            unmatched_city.add(city)
            continue
        by_city[city].append({
            "id": r["id"],
            "name": r["name"],
            "start": r["start"],
            "end": r["end"],
            "schedule": {day: day_sched.get(day) for day in DAY_TYPES},
        })
        joined += 1

    if unmatched_city:
        print(f"경고: 시도 매핑 없는 지자체 {sorted(unmatched_city)}")

    cities = {}
    for city, city_routes in by_city.items():
        city_routes.sort(key=lambda r: r["name"])
        cities[city] = {
            "sido": SIGUNGU_TO_SIDO[city],
            "routes": city_routes,
        }

    total_routes = sum(len(c["routes"]) for c in cities.values())
    print(f"조인 완료: {joined}개 노선 -> {len(cities)}개 지자체 (총 {total_routes}개 노선)")

    OUT_JSON.write_text(json.dumps({"cities": cities}, ensure_ascii=False, indent=None), encoding="utf-8")
    print(f"저장: {OUT_JSON} ({OUT_JSON.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
