# -*- coding: utf-8 -*-
"""
data/express_routes.json + suburbs_routes.json -> 고속버스/시외버스 페이지 생성
generate_pages.py(지역 시내버스) 다음에 실행할 것 — sitemap.xml에 URL을 append함.

사용법:
  python scripts/generate_pages.py       (먼저)
  python scripts/generate_express_pages.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

from generate_pages import (  # noqa: E402
    page_head, HEADER_TMPL, HEAD_COMMON, BASE_URL, SITE_NAME, YEAR, TODAY,
    COUPANG_HTML, COUPANG_DISCLOSURE_INLINE, MOBILE_AD,
)

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"

BOOKING_LINKS = {
    "고속버스": ("고속버스 통합예매 (코버스)", "https://www.kobus.co.kr"),
    "시외버스": ("시외버스 통합예매 (버스타고)", "https://www.bustago.or.kr"),
}


def load(name):
    p = DATA_DIR / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def slugify(name, tid):
    base = re.sub(r"[^\w가-힣]", "", name) or "터미널"
    h = hashlib.md5(tid.encode("utf-8")).hexdigest()[:6]
    return f"{base}-{h}"


def fmt_hhmi(v):
    """'YYYYMMDDHHMI' -> 'HH:MI', 형식이 다르면 뒤 4자리만 시도"""
    if v is None:
        return None
    v = str(v)
    if len(v) < 4:
        return None
    tail = v[-4:]
    if not tail.isdigit():
        return None
    return f"{tail[:2]}:{tail[2:]}"


def fmt_won(v):
    try:
        return f"{int(v):,}원"
    except (TypeError, ValueError):
        return v or "-"


def route_stats(route):
    trips = [t for t in route["trips"]]
    dep_times = sorted({fmt_hhmi(t["depTime"]) for t in trips if fmt_hhmi(t["depTime"])})
    charges = []
    for t in trips:
        try:
            charges.append(int(t["charge"]))
        except (TypeError, ValueError):
            pass
    grades = sorted({t["grade"] for t in trips if t.get("grade")})
    return {
        "count": len(trips),
        "first": dep_times[0] if dep_times else None,
        "last": dep_times[-1] if dep_times else None,
        "min_fare": min(charges) if charges else None,
        "max_fare": max(charges) if charges else None,
        "grades": grades,
    }


def eun_neun(word):
    if not word:
        return "는"
    last = word[-1]
    if not ("가" <= last <= "힣"):
        return "는"
    jong = (ord(last) - ord("가")) % 28
    return "는" if jong == 0 else "은"


def ro_euro(word):
    if not word:
        return "으로"
    last = word[-1]
    if not ("가" <= last <= "힣"):
        return "으로"
    jong = (ord(last) - ord("가")) % 28
    return "로" if jong in (0, 8) else "으로"  # 0=받침없음, 8=ㄹ받침


def build_intro(cat_label, dep_nm, arr_nm, stats):
    parts = [f"{dep_nm}에서 {arr_nm}{ro_euro(arr_nm)} 가는 {cat_label} 정보{eun_neun('정보')} 아래와 같습니다."]
    if stats["count"]:
        parts.append(f"하루 총 {stats['count']}회 운행하며, 첫차는 {stats['first']}, 막차는 {stats['last']}입니다.")
    if stats["min_fare"] is not None:
        if stats["min_fare"] == stats["max_fare"]:
            parts.append(f"편도 요금은 {fmt_won(stats['min_fare'])}입니다.")
        else:
            parts.append(f"편도 요금은 등급에 따라 {fmt_won(stats['min_fare'])}~{fmt_won(stats['max_fare'])}입니다.")
    if stats["grades"]:
        parts.append(f"버스 등급: {', '.join(stats['grades'])}.")
    parts.append("실제 배차·요금은 당일 상황에 따라 달라질 수 있어 정확한 예매는 공식 예매사이트에서 확인하세요.")
    return " ".join(parts)


def footer_html(root):
    return f"""{COUPANG_HTML}{COUPANG_DISCLOSURE_INLINE}<footer class="footer" data-root="{root}"></footer>

<script src="{root}js/wooahouse-originals-tool.js"></script>
<script src="{root}js/wooa-sidebar.js"></script>
<script src="{root}js/wooa-footer.js"></script>
</body>
</html>
"""


def route_table_html(route):
    rows = []
    for t in route["trips"]:
        dep = fmt_hhmi(t["depTime"]) or "-"
        arr = fmt_hhmi(t["arrTime"]) or ""
        rows.append(
            f'<tr><td>{dep}</td><td>{arr or "-"}</td><td>{t.get("grade") or "-"}</td>'
            f'<td>{fmt_won(t.get("charge"))}</td></tr>'
        )
    if not rows:
        return '<p style="color:#6B7280;padding:16px 0;">오늘은 조회되는 배차 정보가 없습니다. 공휴일 등 운행 일정은 터미널에 직접 확인하세요.</p>'
    return f"""<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:.92rem;">
  <thead><tr style="text-align:left;color:#6B7280;border-bottom:2px solid #E5E7EB;">
    <th style="padding:8px 6px;">출발</th><th style="padding:8px 6px;">도착</th>
    <th style="padding:8px 6px;">등급</th><th style="padding:8px 6px;">요금</th>
  </tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
</div>"""


def gen_route_page(cat_label, cat_slug, route, book_label, book_url):
    dep_nm, arr_nm = route["depTerminalNm"], route["arrTerminalNm"]
    stats = route_stats(route)
    intro = build_intro(cat_label, dep_nm, arr_nm, stats)

    title = f"{dep_nm}→{arr_nm} {cat_label} 시간표·요금 {YEAR} | {SITE_NAME}"
    fare_txt = (f"{fmt_won(stats['min_fare'])}"
                if stats["min_fare"] and stats["min_fare"] == stats["max_fare"]
                else f"{fmt_won(stats['min_fare'])}~{fmt_won(stats['max_fare'])}" if stats["min_fare"] else "정보없음")
    desc = f"{dep_nm}에서 {arr_nm}까지 {cat_label} 시간표와 요금({fare_txt}). 하루 {stats['count']}회 운행, 첫차·막차 시간을 확인하세요."
    keywords = f"{dep_nm} {arr_nm} {cat_label}, {dep_nm}-{arr_nm} 버스시간표, {dep_nm} {arr_nm} 버스 요금"
    canonical = f"{BASE_URL}/{quote(cat_slug)}/{quote(slugify(dep_nm, route['depTerminalId']))}/{quote(slugify(arr_nm, route['arrTerminalId']))}.html"

    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:760px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;">
    <a href="../../index.html" style="color:#6B7280;">홈</a> ›
    <a href="../index.html" style="color:#6B7280;">{cat_label}</a> ›
    <a href="index.html" style="color:#6B7280;">{dep_nm}</a> › {arr_nm}
  </nav>
  <h1 style="font-size:1.45rem;font-weight:800;margin-bottom:6px;">🚌 {dep_nm} → {arr_nm} {cat_label}</h1>
  <p style="color:#374151;line-height:1.75;margin:12px 0 20px;">{intro}</p>

  {MOBILE_AD}

  <div style="margin:20px 0;">
    <a href="{book_url}" style="display:block;text-align:center;padding:14px;border-radius:10px;background:#0D9488;color:#fff;font-weight:700;text-decoration:none;">🎫 {book_label}에서 예매하기 →</a>
  </div>

  <h2 style="font-size:1.05rem;font-weight:700;margin:24px 0 10px;">오늘({TODAY}) 시간표</h2>
  {route_table_html(route)}

  <details style="margin-top:24px;">
    <summary style="cursor:pointer;font-weight:600;padding:8px 0;">이 페이지에서 예매할 수 있나요?</summary>
    <p style="padding:6px 0;color:#374151;line-height:1.7;">아니요. 우아버스는 시간표·요금 조회 전용이며, 실제 승차권 예매는 {book_label} 또는 해당 터미널에서 진행해주세요.</p>
  </details>
  <details>
    <summary style="cursor:pointer;font-weight:600;padding:8px 0;">시간표가 매일 똑같나요?</summary>
    <p style="padding:6px 0;color:#374151;line-height:1.7;">공휴일·연휴 등에는 배차가 달라질 수 있습니다. 이 페이지는 매일 자동 갱신되지만, 중요한 일정이라면 출발 전 {book_label}에서 다시 확인하세요.</p>
  </details>

  <div style="margin-top:28px;padding:16px;border:1px dashed #E5E7EB;border-radius:10px;text-align:center;">
    <a href="index.html" style="color:#0D9488;font-weight:600;text-decoration:none;">📍 {dep_nm} 출발 다른 노선 보기 →</a>
  </div>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{"@type":"Question","name":"이 페이지에서 예매할 수 있나요?","acceptedAnswer":{{"@type":"Answer","text":"아니요. 우아버스는 시간표·요금 조회 전용이며, 실제 승차권 예매는 {book_label} 또는 해당 터미널에서 진행해주세요."}}}},
      {{"@type":"Question","name":"시간표가 매일 똑같나요?","acceptedAnswer":{{"@type":"Answer","text":"공휴일·연휴 등에는 배차가 달라질 수 있습니다. 이 페이지는 매일 자동 갱신되지만, 중요한 일정이라면 출발 전 공식 예매사이트에서 다시 확인하세요."}}}}
    ]
  }}
  </script>
</div>
"""
    head = page_head(title, desc, keywords, canonical, "../../", "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../../") + "\n" + body + footer_html("../../")


def gen_terminal_page(cat_label, cat_slug, term_nm, term_id, routes_from, book_label, book_url):
    title = f"{term_nm} {cat_label} 시간표 — 전체 노선 | {SITE_NAME}"
    desc = f"{term_nm}에서 출발하는 {cat_label} 전체 노선 {len(routes_from)}개, 목적지별 시간표·요금을 확인하세요."
    canonical = f"{BASE_URL}/{quote(cat_slug)}/{quote(slugify(term_nm, term_id))}/index.html"

    routes_from = sorted(routes_from, key=lambda r: r["arrTerminalNm"])
    rows = []
    for r in routes_from:
        st = route_stats(r)
        fare = (fmt_won(st["min_fare"]) if st["min_fare"] and st["min_fare"] == st["max_fare"]
                else f'{fmt_won(st["min_fare"])}~' if st["min_fare"] else "-")
        arr_slug = slugify(r["arrTerminalNm"], r["arrTerminalId"])
        rows.append(f"""<a href="{quote(arr_slug)}.html" style="display:flex;justify-content:space-between;align-items:center;
      padding:12px 14px;border:1px solid #E5E7EB;border-radius:10px;margin-bottom:8px;text-decoration:none;color:inherit;">
      <span style="font-weight:600;">{r['arrTerminalNm']}</span>
      <span style="font-size:.85rem;color:#6B7280;">일 {st['count']}회 · {fare}</span>
    </a>""")

    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:760px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;">
    <a href="../../index.html" style="color:#6B7280;">홈</a> ›
    <a href="../index.html" style="color:#6B7280;">{cat_label}</a> › {term_nm}
  </nav>
  <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:6px;">🚏 {term_nm} {cat_label} 시간표</h1>
  <p style="color:#6B7280;font-size:.92rem;margin-bottom:20px;">{term_nm}에서 출발하는 노선 {len(routes_from)}개</p>

  {MOBILE_AD}

  <div>{"".join(rows) if rows else '<p style="color:#6B7280;">등록된 노선이 없습니다.</p>'}</div>

  <div style="margin:24px 0;">
    <a href="{book_url}" style="display:block;text-align:center;padding:14px;border-radius:10px;background:#F3F4F6;color:#0D9488;font-weight:700;text-decoration:none;">🎫 {book_label} 바로가기 →</a>
  </div>
</div>
"""
    head = page_head(title, desc, f"{term_nm} {cat_label}, {term_nm} 버스시간표", canonical, "../../", "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../../") + "\n" + body + footer_html("../../")


def gen_category_index(cat_label, cat_slug, terminals_with_routes, book_label, book_url):
    title = f"전국 {cat_label} 시간표·요금 검색 {YEAR} | {SITE_NAME}"
    desc = f"전국 {cat_label} 터미널·노선별 시간표와 요금을 한눈에 검색하세요. 출발지와 도착지를 선택하면 오늘 배차 정보를 바로 확인할 수 있습니다."
    canonical = f"{BASE_URL}/{quote(cat_slug)}/index.html"

    term_options = "".join(
        f'<option value="{quote(slugify(nm, tid))}">{nm}</option>'
        for tid, nm in sorted(terminals_with_routes, key=lambda x: x[1])
    )

    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:760px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;"><a href="../index.html" style="color:#6B7280;">홈</a> › {cat_label}</nav>
  <h1 style="font-size:1.5rem;font-weight:800;margin-bottom:8px;">🚌 전국 {cat_label} 시간표</h1>
  <p style="color:#6B7280;margin-bottom:20px;">출발 터미널을 선택하면 해당 터미널에서 가는 전체 노선을 볼 수 있어요.</p>

  {MOBILE_AD}

  <div style="background:#F9FAFB;border-radius:12px;padding:18px;margin:16px 0 28px;">
    <label style="font-size:.85rem;font-weight:600;color:#374151;">출발 터미널</label>
    <select id="depSel" style="width:100%;padding:10px;margin:6px 0 12px;border-radius:8px;border:1px solid #E5E7EB;">
      <option value="">터미널을 선택하세요</option>
      {term_options}
    </select>
    <button onclick="goTerminal()" style="width:100%;padding:12px;border:none;border-radius:8px;background:#0D9488;color:#fff;font-weight:700;cursor:pointer;">노선 보기</button>
  </div>

  <p style="font-size:.85rem;color:#6B7280;">전국 {len(terminals_with_routes)}개 터미널의 {cat_label} 정보를 제공합니다. 매일 자동으로 새로운 노선이 추가되고 있습니다.</p>

  <div style="margin:24px 0;">
    <a href="{book_url}" style="display:block;text-align:center;padding:14px;border-radius:10px;background:#F3F4F6;color:#0D9488;font-weight:700;text-decoration:none;">🎫 {book_label} 바로가기 →</a>
  </div>
</div>
<script>
function goTerminal(){{
  var v = document.getElementById('depSel').value;
  if(!v) return;
  location.href = v + '/index.html';
}}
</script>
"""
    head = page_head(title, desc, f"전국 {cat_label} 시간표, {cat_label} 요금", canonical, "../", "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../") + "\n" + body + footer_html("../")


def process_category(cat_label, cat_slug, routes_file):
    routes = load(routes_file)
    routes = [r for r in routes if r.get("trips")]  # 오늘 배차 없는 건 목록에서 제외(페이지 자체는 유지 X, 재탐색 대상)
    print(f"=== {cat_label}: 노선 {len(routes)}개 (배차 있음) ===")
    if not routes:
        return [], 0

    cat_dir = DOCS_DIR / cat_slug
    cat_dir.mkdir(parents=True, exist_ok=True)
    book_label, book_url = BOOKING_LINKS[cat_label]

    by_dep = {}
    for r in routes:
        by_dep.setdefault((r["depTerminalId"], r["depTerminalNm"]), []).append(r)

    urls = [f"  <url><loc>{BASE_URL}/{cat_slug}/index.html</loc><changefreq>daily</changefreq><priority>0.8</priority></url>"]

    generated = 0
    for (dep_id, dep_nm), rlist in by_dep.items():
        dep_slug = slugify(dep_nm, dep_id)
        term_dir = cat_dir / dep_slug
        term_dir.mkdir(parents=True, exist_ok=True)
        (term_dir / "index.html").write_text(
            gen_terminal_page(cat_label, cat_slug, dep_nm, dep_id, rlist, book_label, book_url),
            encoding="utf-8",
        )
        urls.append(f"  <url><loc>{BASE_URL}/{cat_slug}/{quote(dep_slug)}/index.html</loc><changefreq>daily</changefreq><priority>0.6</priority></url>")
        generated += 1
        for r in rlist:
            arr_slug = slugify(r["arrTerminalNm"], r["arrTerminalId"])
            (term_dir / f"{arr_slug}.html").write_text(
                gen_route_page(cat_label, cat_slug, r, book_label, book_url), encoding="utf-8",
            )
            urls.append(f"  <url><loc>{BASE_URL}/{cat_slug}/{quote(dep_slug)}/{quote(arr_slug)}.html</loc><changefreq>daily</changefreq><priority>0.7</priority></url>")
            generated += 1

    terminals_with_routes = list(by_dep.keys())
    terminals_with_routes = [(tid, nm) for (tid, nm) in terminals_with_routes]
    (cat_dir / "index.html").write_text(
        gen_category_index(cat_label, cat_slug, terminals_with_routes, book_label, book_url),
        encoding="utf-8",
    )
    generated += 1

    print(f"  {generated}개 페이지 생성 ({len(by_dep)}개 터미널)")
    return urls, generated


def merge_sitemap(extra_urls):
    sm_path = DOCS_DIR / "sitemap.xml"
    text = sm_path.read_text(encoding="utf-8")
    insert = "\n".join(extra_urls) + "\n"
    text = text.replace("</urlset>", insert + "</urlset>")
    sm_path.write_text(text, encoding="utf-8")


def main():
    total = 0
    all_urls = []
    for cat_label, cat_slug, routes_file in [
        ("고속버스", "고속버스", "express_routes.json"),
        ("시외버스", "시외버스", "suburbs_routes.json"),
    ]:
        urls, n = process_category(cat_label, cat_slug, routes_file)
        all_urls.extend(urls)
        total += n
    merge_sitemap(all_urls)
    print(f"\n총 {total}개 고속/시외버스 페이지 생성, sitemap {len(all_urls)}개 URL 추가")


if __name__ == "__main__":
    main()
