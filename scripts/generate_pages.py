# -*- coding: utf-8 -*-
"""data/routes.json -> 우아버스(WooaBus) 정적 HTML 페이지 생성"""
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "routes.json"
DOCS_DIR = ROOT / "docs"
REGION_DIR = DOCS_DIR / "region"
BASE_URL = "https://wooabus.wooahouse.com"
TODAY = date.today().isoformat()
YEAR = TODAY[:4]
SITE_NAME = "우아버스"
AD_CLIENT = "ca-pub-6464921081676309"
SOURCE_NAME = "한국교통안전공단_버스 노선 및 시간표 정보"

SIDO_SHORT = {
    "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
}

DAY_TYPES = ["매일", "평일", "토요일", "공휴일"]



# 쿠팡 파트너스 (고객 관심 기반 추천) — 콘텐츠·애드센스 아래, 페이지 최하단. 고지 문구는 푸터에 표기.
COUPANG_HTML = '''
<div class="coupang-partners" style="margin:36px auto 0;max-width:720px;padding:0 16px 8px;text-align:center;overflow-x:auto;">
  <script src="https://ads-partners.coupang.com/g.js"></script>
  <script>
    new PartnersCoupang.G({"id":980427,"trackingCode":"AF5600192","subId":"bus","template":"carousel","width":"680","height":"140"});
  </script>
</div>
'''
COUPANG_DISCLOSURE = '    <p style="margin:6px 0 0;font-size:.7rem;opacity:.55;">이 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>\n'
COUPANG_DISCLOSURE_INLINE = '<p style="max-width:720px;margin:6px auto 24px;text-align:center;font-size:.7rem;opacity:.55;padding:0 16px;">이 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>\n'

def short_name(name):
    if len(name) > 2 and name[-1] in "구군시":
        return name[:-1]
    return name


HEAD_COMMON = """<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<meta name="theme-color" content="#0D9488">
"""

HEADER_TMPL = """<header>
  <div class="header-inner">
    <a href="{root}index.html" class="logo">🚌 WooaBus</a>
    <nav>
      <a href="{root}index.html#region">지역별 시간표</a>
      <a href="{root}고속버스/index.html">고속버스</a>
      <a href="{root}시외버스/index.html">시외버스</a>
      <a href="{root}about.html">소개</a>
    </nav>
  </div>
</header>

<script src="{root}js/wooa-sites-bar.js"></script>
<script src="{root}js/ad-dev-placeholder.js"></script>
"""

MOBILE_AD = """<div class="mobile-top-ad">
  <ins class="adsbygoogle" style="display:block;width:100%;min-height:60px"
    data-ad-client="ca-pub-6464921081676309"
    data-ad-slot="7080296704"
    data-ad-format="auto"
    data-full-width-responsive="true"></ins>
  <script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>
</div>"""

MID_AD = """<div style="margin:24px 0;">
<ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704" data-ad-format="auto" data-full-width-responsive="true"></ins>
<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>
</div>"""


def page_head(title, desc, keywords, canonical, root, extra_ld=""):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
{HEAD_COMMON}
  <meta name="naver-site-verification" content="8bdef723dac0fc357e0c6f1105a7656b0787bd6c" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%9A%8C%3C/text%3E%3C/svg%3E">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="keywords" content="{keywords}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:locale" content="ko_KR">
  <meta property="og:image" content="{BASE_URL}/og-image.png">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
{extra_ld}
  <link rel="stylesheet" href="{root}css/style.css">
</head>
"""


def fmt_time(t):
    return t if t else None


def fmt_time_range(day):
    if not day:
        return None
    times = day.get("times")
    if times:
        if len(times) <= 4:
            return ", ".join(times)
        return f"{times[0]} ~ {times[-1]}"
    sf, sl = day.get("start_first", ""), day.get("start_last", "")
    if not sf:
        return None
    if sf == sl:
        return sf
    return f"{sf} ~ {sl}"


def fmt_interval(day):
    if not day:
        return None
    mn, mx = day.get("min_interval", ""), day.get("max_interval", "")
    if mn in ("", "0") and mx in ("", "0"):
        return None
    if mn == mx:
        return f"{mn}분 간격"
    return f"{mn}~{mx}분 간격"


def route_row_html(route):
    s = route["schedule"]
    name = route["name"] or "-"
    start = route["start"] or "-"
    end = route["end"] or "-"
    path = f"{start} → {end}" if start != end else start

    daily = s.get("매일")
    if daily:
        time_html = f'<span class="route-time">{fmt_time_range(daily) or "-"}</span><span class="route-sub">첫차 기준 · 일 {daily.get("trips","-")}회</span>'
        weekend_html = '<span class="day-badge daily">매일 동일</span>'
        interval_html = fmt_interval(daily) or "-"
        search_blob = f"{name} {start} {end} 매일"
    else:
        weekday = s.get("평일")
        sat = s.get("토요일")
        hol = s.get("공휴일")
        weekend = sat or hol
        wd_time = fmt_time_range(weekday)
        we_time = fmt_time_range(weekend)
        trips = weekday.get("trips") if weekday else (weekend.get("trips") if weekend else "-")
        time_html = f'<span class="route-time">{wd_time or "-"}</span><span class="route-sub">첫차 기준 · 일 {trips}회</span>'

        if not weekend:
            weekend_html = '<span class="day-badge weekend-none">주말 미운행</span>'
        elif wd_time == we_time:
            weekend_html = '<span class="day-badge weekend-same">평일과 동일</span>'
        else:
            weekend_html = f'<span class="day-badge weekend-diff">{we_time or "-"}</span>'

        interval_html = fmt_interval(weekday) or fmt_interval(weekend) or "-"
        search_blob = f"{name} {start} {end} 평일 토요일 공휴일"

    return f"""<tr data-search="{search_blob.lower()}">
      <td><span class="route-name">{name}</span></td>
      <td><span class="route-path">{path}</span></td>
      <td>{time_html}</td>
      <td>{weekend_html}</td>
      <td>{interval_html}</td>
    </tr>"""


FILTER_SCRIPT = """<script>
function filterRoutes(){
  var q = document.getElementById('routeSearch').value.trim().toLowerCase();
  var rows = document.querySelectorAll('#routeTable tbody tr');
  var shown = 0;
  rows.forEach(function(tr){
    var match = tr.dataset.search.indexOf(q) !== -1;
    tr.style.display = match ? '' : 'none';
    if (match) shown++;
  });
  document.getElementById('routeCount').textContent = shown + '개 노선';
  document.getElementById('noResult').style.display = shown === 0 ? '' : 'none';
}
</script>"""


def gen_city_page(sido, sigungu, routes):
    short_sido = SIDO_SHORT.get(sido, sido)
    short_sg = short_name(sigungu)
    rows_html = "".join(route_row_html(r) for r in routes)

    body = f"""<div class="form-hero">
  <span class="cat-badge">{sido}</span>
  <h1>🚌 {sido} {sigungu} 버스 시간표</h1>
  <p>{sigungu} 시내·농어촌버스 전체 {len(routes)}개 노선의 첫차·막차 시간을 확인하세요</p>
</div>

<div class="page-with-sidebar">
<div class="form-content">

  <div class="breadcrumb">
    <a href="../../index.html">홈</a> &rsaquo; <a href="../{sido}.html">{sido}</a> &rsaquo; {sigungu}
  </div>

  <div class="info-grid">
    <div class="info-card"><div class="label">지역</div><div class="value">{sido} {sigungu}</div></div>
    <div class="info-card"><div class="label">전체 노선 수</div><div class="value">{len(routes)}개</div></div>
    <div class="info-card"><div class="label">운영기관</div><div class="value">한국교통안전공단 (TS-BIS)</div></div>
    <div class="info-card"><div class="label">데이터 기준일</div><div class="value">{TODAY}</div></div>
  </div>

  {MID_AD}

  <p class="section-title">🔍 노선 검색</p>
  <input type="text" id="routeSearch" class="route-search" placeholder="노선번호 또는 정류장 이름으로 검색 (예: 100, {short_sg}터미널)" oninput="filterRoutes()">
  <p class="route-count" id="routeCount">{len(routes)}개 노선</p>

  <div class="route-table-wrap">
    <table class="route-table" id="routeTable">
      <thead>
        <tr>
          <th>노선</th>
          <th>기점 → 종점</th>
          <th>운행시간(평일)</th>
          <th>주말·공휴일</th>
          <th>배차간격</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div class="no-result" id="noResult" style="display:none;">검색 결과가 없습니다.</div>
  </div>

  {FILTER_SCRIPT}

  <div class="wooa-orig-anchor"></div>

  <div class="tips-panel">
    <h3>💡 Tips</h3>
    <ul>
      <li>시간은 모두 <strong>기점(출발지) 첫차 출발시각</strong> 기준입니다. 중간 정류장은 노선 배차간격만큼 늦게 도착합니다.</li>
      <li>'주말 미운행' 노선은 평일에만 운행하니 주말 이용 시 반드시 확인하세요.</li>
      <li>실제 도착시간은 도로 상황에 따라 몇 분씩 달라질 수 있어, 여유있게 미리 나가는 것을 추천합니다.</li>
    </ul>
  </div>

  <div class="faq-section">
    <h2>자주 묻는 질문</h2>
    <details>
      <summary>{sigungu} 버스 막차는 몇 시인가요?</summary>
      <p>노선마다 막차 시간이 다릅니다. 위 표에서 이용하실 노선을 검색하면 첫차·막차 운행시간을 확인할 수 있습니다. 일반적으로 오후 9~10시 사이가 많지만, 배차가 적은 노선은 오후 6~7시에 막차가 끊기는 경우도 있으니 꼭 확인하세요.</p>
    </details>
    <details>
      <summary>주말이나 공휴일에도 버스가 다니나요?</summary>
      <p>노선별로 다릅니다. 표에서 '평일과 동일'로 표시된 노선은 주말에도 같은 시간에 운행하고, '주말 미운행'으로 표시된 노선은 평일에만 다닙니다. 시간이 다르게 표시된 노선은 주말 전용 시간표를 별도로 확인하세요.</p>
    </details>
    <details>
      <summary>이 시간표는 정확한가요? 실제와 다를 수 있나요?</summary>
      <p>본 정보는 한국교통안전공단이 운영하는 버스정보시스템(TS-BIS) 공공데이터를 기준으로 제공합니다. 노선 개편이나 임시 운행 변경이 있을 경우 실제 시간과 차이가 있을 수 있으니, 중요한 일정이라면 해당 지자체 교통과 또는 버스회사에 최종 확인하시길 권장합니다.</p>
    </details>
    <details>
      <summary>이 사이트에서 버스표를 예매할 수 있나요?</summary>
      <p>이 페이지(시내·농어촌버스)는 예매 없이 정류장에서 바로 승차하시면 됩니다. 고속버스·시외버스는 별도로 <a href="../../고속버스/index.html">고속버스</a>·<a href="../../시외버스/index.html">시외버스</a> 시간표 페이지에서 예매 사이트로 연결해드립니다.</p>
    </details>
  </div>

</div>
<aside class="tool-sidebar"></aside>
</div>

{COUPANG_HTML}{COUPANG_DISCLOSURE_INLINE}<footer class="footer" data-root="../../"></footer>

<script src="../../js/wooahouse-originals-tool.js"></script>
<script src="../../js/wooa-sidebar.js"></script>
<script src="../../js/wooa-footer.js"></script>
</body>
</html>
"""
    canonical = f"{BASE_URL}/region/{quote(sido)}/{quote(sigungu)}.html"
    title = f"{sido} {sigungu} 버스시간표 {YEAR} | {SITE_NAME}"
    desc = f"{sido} {sigungu}({short_sg}) 시내·농어촌버스 {len(routes)}개 노선 첫차·막차 시간을 노선번호로 검색하세요. 평일·주말·공휴일 운행시간 정보 제공."
    keywords = f"{sigungu} 버스시간표, {short_sg}버스시간표, {sigungu} 버스 첫차 막차, {sido} {sigungu} 버스노선, {short_sg} 시내버스 시간표"

    faq_ld_items = [
        (f"{sigungu} 버스 막차는 몇 시인가요?", f"노선마다 다릅니다. 우아버스에서 {sigungu} 노선번호를 검색하면 첫차·막차 시간을 바로 확인할 수 있습니다."),
        ("주말이나 공휴일에도 버스가 다니나요?", "노선별로 다릅니다. 표에서 평일과 동일 여부, 주말 미운행 여부를 노선마다 표시하고 있습니다."),
    ]
    faq_ld = ",\n      ".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}' % (json.dumps(q, ensure_ascii=False), json.dumps(a, ensure_ascii=False))
        for q, a in faq_ld_items
    )
    extra_ld = f"""  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {faq_ld}
    ]
  }}
  </script>"""

    head = page_head(title, desc, keywords, canonical, "../../", extra_ld)
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../../") + "\n" + body


GRID_STYLE = "display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;"


def gen_sido_page(sido, city_map):
    cities = sorted(city_map.keys())
    cards = "".join(
        f"""<a href="{sido}/{sg}.html" class="form-card">
          <span class="form-icon">🚌</span>
          <div class="form-name">{sg}</div>
          <div class="form-desc">{len(city_map[sg])}개 노선</div>
        </a>"""
        for sg in cities
    )
    total_routes = sum(len(r) for r in city_map.values())
    short_sido = SIDO_SHORT.get(sido, sido)
    body = f"""<div class="form-hero">
  <span class="cat-badge">{SITE_NAME}</span>
  <h1>🚌 {sido} 버스 시간표</h1>
  <p>{sido} 내 {len(cities)}개 시·군의 버스 시간표를 확인하세요</p>
</div>

<div class="page-with-sidebar">
<div class="form-content">

  <div class="breadcrumb">
    <a href="../index.html">홈</a> &rsaquo; {sido}
  </div>

  <div class="info-grid">
    <div class="info-card"><div class="label">시·군</div><div class="value">{len(cities)}개</div></div>
    <div class="info-card"><div class="label">전체 노선</div><div class="value">{total_routes:,}개</div></div>
  </div>

  {MID_AD}

  <p class="section-title">{short_sido} 시·군 선택</p>
  <div class="forms-grid">
  {cards}
  </div>

</div>
<aside class="tool-sidebar"></aside>
</div>

{COUPANG_HTML}{COUPANG_DISCLOSURE_INLINE}<footer class="footer" data-root="../"></footer>

<script src="../js/wooahouse-originals-tool.js"></script>
<script src="../js/wooa-sidebar.js"></script>
<script src="../js/wooa-footer.js"></script>
</body>
</html>
"""
    canonical = f"{BASE_URL}/region/{quote(sido)}.html"
    title = f"{sido} 버스시간표 지역별 조회 | {SITE_NAME}"
    desc = f"{sido}({short_sido}) 내 {len(cities)}개 시·군 버스 시간표를 확인하세요. {', '.join(cities[:5])} 등."
    keywords = f"{sido} 버스시간표, {short_sido} 버스시간표, {sido} 시내버스, {sido} 농어촌버스"
    head = page_head(title, desc, keywords, canonical, "../")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../") + "\n" + body


def gen_index(sido_map):
    total_sido = len(sido_map)
    total_city = sum(len(c) for c in sido_map.values())
    total_routes = sum(len(routes) for cities in sido_map.values() for routes in cities.values())

    stats_bar = f"""<div class="stats-bar">
  <div class="stat-card"><div class="num">{total_sido}</div><div class="label">개 도(道)</div></div>
  <div class="stat-card"><div class="num">{total_city}</div><div class="label">개 시·군</div></div>
  <div class="stat-card"><div class="num">{total_routes:,}</div><div class="label">개 버스 노선</div></div>
  <div class="stat-card"><div class="num">매달</div><div class="label">자동 업데이트</div></div>
</div>"""

    sections = []
    for sido in sorted(sido_map.keys()):
        cities = sido_map[sido]
        cards = "".join(
            f"""<a href="region/{sido}/{sg}.html" class="form-card">
              <span class="form-icon">🚌</span>
              <div class="form-name">{sg}</div>
              <div class="form-desc">{len(routes)}개 노선</div>
            </a>"""
            for sg, routes in sorted(cities.items())
        )
        sections.append(f"""
        <div class="category-block" id="{sido}">
          <div class="category-header">
            <div class="category-dot" style="background:var(--primary);"></div>
            <div>
              <p class="category-title">{sido}</p>
              <p class="category-desc">{len(cities)}개 시·군</p>
            </div>
          </div>
          <div class="forms-grid">{cards}</div>
        </div>""")

    body = f"""<div class="hero">
  <h1>🚌 전국 중소도시 버스 시간표</h1>
  <p>카카오버스·네이버지도에 잘 안 나오는 소도시·농어촌 시내버스 첫차·막차 시간을 노선별로 확인하세요</p>
  <div class="hero-tags">
    <a href="#region" class="hero-tag">지역별 시간표 보기 ↓</a>
  </div>
</div>
{stats_bar}
<div style="max-width:1100px;margin:24px auto 0;padding:0 20px;">
  {MID_AD}
</div>

<div class="index-with-sidebar">
  <div style="min-width:0;">
    <p class="section-title" id="region">지역 선택 ({total_sido}개 도 · {total_city}개 시·군)</p>
    {''.join(sections)}

    <div class="faq-section" style="margin-top:40px;">
      <h2>자주 묻는 질문</h2>
      <details>
        <summary>왜 서울·부산 같은 대도시는 없나요?</summary>
        <p>서울, 부산 등 대도시는 자체 버스정보시스템(BIS)과 카카오버스·네이버지도 실시간 조회가 이미 잘 되어 있습니다. 우아버스는 자체 BIS가 없어 정보를 찾기 어려운 중소도시·농어촌 지역(52개 시·군)의 버스 시간표만 전문적으로 제공합니다.</p>
      </details>
      <details>
        <summary>우리 지역이 목록에 없어요.</summary>
        <p>우아버스는 한국교통안전공단이 운영하는 버스정보시스템(TS-BIS)에 등록된 지역만 제공합니다. 현재 목록에 없는 지역은 아직 TS-BIS에 편입되지 않았거나, 별도의 자체 시스템을 운영 중인 지역일 수 있습니다.</p>
      </details>
      <details>
        <summary>정보 출처는 어디인가요?</summary>
        <p>공공데이터포털(data.go.kr)에 공개된 '{SOURCE_NAME}' 데이터를 기반으로 합니다. 데이터는 한국교통안전공단이 관리하며, 매달 최신 데이터로 업데이트합니다.</p>
      </details>
    </div>
  </div>
  <aside class="index-sidebar"></aside>
</div>

{COUPANG_HTML}{COUPANG_DISCLOSURE_INLINE}<footer class="footer" data-root=""></footer>

<script src="js/wooahouse-originals-tool.js"></script>
<script src="js/wooa-sidebar.js"></script>
<script src="js/wooa-footer.js"></script>
</body>
</html>
"""
    title = f"전국 소도시 버스 시간표 조회 — 시내버스·농어촌버스 첫차 막차 | {SITE_NAME}"
    desc = f"전국 {total_city}개 중소도시·농어촌 지역의 시내버스 시간표를 노선별로 무료 조회하세요. 첫차·막차, 배차간격, 평일·주말 운행정보 제공. 총 {total_routes:,}개 노선."
    keywords = "버스시간표, 시내버스 시간표, 농어촌버스 시간표, 첫차 막차, 소도시 버스시간표, 군내버스 시간표"
    head = page_head(title, desc, keywords, f"{BASE_URL}/", "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="") + "\n" + MOBILE_AD + "\n" + body


def gen_sitemap(sido_map):
    urls = [f"  <url><loc>{BASE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>"]
    for sido, cities in sido_map.items():
        urls.append(f"  <url><loc>{BASE_URL}/region/{quote(sido)}.html</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>")
        for sg in cities:
            urls.append(f"  <url><loc>{BASE_URL}/region/{quote(sido)}/{quote(sg)}.html</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    (DOCS_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    cities = data["cities"]
    print(f"{len(cities)}개 지자체 로드")

    sido_map = {}
    for city, info in cities.items():
        sido_map.setdefault(info["sido"], {})[city] = info["routes"]

    generated = 0
    for sido, city_map in sido_map.items():
        sido_dir = REGION_DIR / sido
        sido_dir.mkdir(parents=True, exist_ok=True)
        (REGION_DIR / f"{sido}.html").write_text(gen_sido_page(sido, city_map), encoding="utf-8")
        generated += 1
        for sg, routes in city_map.items():
            (sido_dir / f"{sg}.html").write_text(gen_city_page(sido, sg, routes), encoding="utf-8")
            generated += 1

    (DOCS_DIR / "index.html").write_text(gen_index(sido_map), encoding="utf-8")
    generated += 1

    gen_sitemap(sido_map)
    print(f"총 {generated}개 페이지 생성 완료")


if __name__ == "__main__":
    main()
