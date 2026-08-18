(function () {
  const SITES = [
    { host: 'pdfkit.wooahouse.com',      color: '#FF4444', icon: '📄', name: 'WooaPDF',     title: '무료 온라인 PDF 도구 모음',        url: 'https://pdfkit.wooahouse.com' },
    { host: 'imagekit.wooahouse.com',     color: '#6366F1', icon: '🖼️', name: 'WooaImage',  title: '무료 온라인 이미지 도구 모음',     url: 'https://imagekit.wooahouse.com' },
    { host: 'colorkit.wooahouse.com',     color: '#F59E0B', icon: '🎨', name: 'WooaColor',  title: '색상 추출·변환·팔레트 생성',       url: 'https://colorkit.wooahouse.com' },
    { host: 'textkit.wooahouse.com',      color: '#10B981', icon: '✏️', name: 'WooaText',  title: '텍스트 변환·정렬·편집 도구',       url: 'https://textkit.wooahouse.com' },
    { host: 'qrkit.wooahouse.com',        color: '#3B82F6', icon: '📱', name: 'WooaQR',     title: 'QR 코드 생성·스캔',                url: 'https://qrkit.wooahouse.com' },
    { host: 'calckit.wooahouse.com',      color: '#8B5CF6', icon: '🧮', name: 'WooaCalc',   title: '단위 변환·수식 계산기',            url: 'https://calckit.wooahouse.com' },
    { host: 'fontkit.wooahouse.com',      color: '#EC4899', icon: '🔤', name: 'WooaFont',   title: '무료 상업용 폰트 모음',            url: 'https://fontkit.wooahouse.com' },
    { host: 'mactools.wooahouse.com',     color: '#6B7280', icon: '🍎', name: 'WooaMac',    title: '맥 필수 앱 모음',                  url: 'https://mactools.wooahouse.com' },
    { host: 'pctools.wooahouse.com',      color: '#0EA5E9', icon: '🖥️', name: 'WooaPC',    title: '포맷 후 필수 프로그램 모음',       url: 'https://pctools.wooahouse.com' },
    { host: 'vskit.wooahouse.com',        color: '#007ACC', icon: '💻', name: 'WooaVS',     title: 'VS Code 확장 프로그램 모음',       url: 'https://vskit.wooahouse.com' },
    { host: 'wooaaudio.wooahouse.com',    color: '#F97316', icon: '🎵', name: 'WooaAudio',  title: '온라인 오디오 도구',               url: 'https://wooaaudio.wooahouse.com' },
    { host: 'wooavideo.wooahouse.com',    color: '#EF4444', icon: '🎬', name: 'WooaVideo',  title: '온라인 비디오 도구',               url: 'https://wooavideo.wooahouse.com' },
    { host: 'wooaviewer.wooahouse.com',   color: '#14B8A6', icon: '🔍', name: 'WooaViewer', title: '파일 뷰어 모음',                   url: 'https://wooaviewer.wooahouse.com' },
    { host: 'wooadev.wooahouse.com',      color: '#64748B', icon: '🛠️', name: 'WooaDev',   title: '개발자 도구 모음',                 url: 'https://wooadev.wooahouse.com' },
    { host: 'wooaocr.wooahouse.com',      color: '#A855F7', icon: '🔎', name: 'WooaOCR',    title: 'OCR 이미지 텍스트 추출',           url: 'https://wooaocr.wooahouse.com' },
    { host: 'wooasheet.wooahouse.com',    color: '#22C55E', icon: '📊', name: 'WooaSheet',  title: '온라인 스프레드시트 도구',         url: 'https://wooasheet.wooahouse.com' },
    { host: 'wooaseo.wooahouse.com',      color: '#F59E0B', icon: '🔎', name: 'WooaSEO',    title: 'SEO 분석 도구',                    url: 'https://wooaseo.wooahouse.com' },
    { host: 'wooagosa.wooahouse.com',     color: '#6366F1', icon: '📝', name: 'WooaGosa',   title: '자격증·면허 무료 모의고사',        url: 'https://wooagosa.wooahouse.com' },
  ];

  function bgLuminance() {
    const bg = getComputedStyle(document.body).backgroundColor;
    const m = bg.match(/\d+/g);
    if (!m || m.length < 3) return 255;
    return 0.299 * +m[0] + 0.587 * +m[1] + 0.114 * +m[2];
  }
  const dark = bgLuminance() < 80;

  const currentHost = window.location.hostname;
  const utmSource = currentHost.replace('.wooahouse.com', '');
  const picks = SITES
    .filter(s => s.host !== currentHost)
    .sort(() => Math.random() - 0.5)
    .slice(0, 4);

  if (!picks.length) return;

  const style = document.createElement('style');
  style.textContent = `
    .wooa-tool-wrap {
      margin: 32px 0 24px;
    }
    .wooa-tool-heading {
      font-size: 1rem;
      font-weight: 700;
      margin: 0 0 14px;
      color: ${dark ? '#e2e8f0' : '#1F2937'};
      padding-bottom: 8px;
      border-bottom: 2px solid #3B82F6;
    }
    .wooa-tool-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }
    @media (max-width: 600px) {
      .wooa-tool-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .wooa-tool-card {
      background: ${dark ? '#1e293b' : '#F9FAFB'};
      border: 1px solid ${dark ? '#334155' : '#E5E7EB'};
      border-radius: 10px;
      padding: 14px 10px;
      text-decoration: none;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      text-align: center;
      position: relative;
      overflow: hidden;
      transition: border-color .2s, transform .2s;
      font-size: .8rem;
      font-weight: 500;
    }
    .wooa-tool-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: var(--wooa-color);
    }
    .wooa-tool-card:hover {
      border-color: var(--wooa-color);
      transform: translateY(-2px);
    }
    .wooa-tool-icon {
      font-size: 1.4rem;
      line-height: 1;
    }
    .wooa-tool-name {
      font-size: .82rem;
      font-weight: 700;
      color: var(--wooa-color);
      line-height: 1.2;
    }
    .wooa-tool-title {
      font-size: .72rem;
      font-weight: 400;
      color: ${dark ? '#94a3b8' : '#6B7280'};
      line-height: 1.3;
    }
  `;
  document.head.appendChild(style);

  // ── 인콘텐츠 광고 ──────────────────────────────────────────
  const adWrap = document.createElement('div');
  adWrap.style.cssText = 'margin: 0 auto 32px; max-width: 800px; padding: 0 1rem;';
  const ins = document.createElement('ins');
  ins.className = 'adsbygoogle';
  ins.style.cssText = 'display:block';
  ins.setAttribute('data-ad-client', 'ca-pub-6464921081676309');
  ins.setAttribute('data-ad-slot', '6255378195');
  ins.setAttribute('data-ad-format', 'auto');
  ins.setAttribute('data-full-width-responsive', 'true');
  adWrap.appendChild(ins);

  // ── 위젯 ───────────────────────────────────────────────────
  const wrap = document.createElement('div');
  wrap.className = 'wooa-tool-wrap';
  wrap.innerHTML = `
    <h2 class="wooa-tool-heading">🛠️ 다른 작업도 여기서 해결하세요</h2>
    <div class="wooa-tool-grid">
      ${picks.map(s => `
        <a href="${s.url}?utm_source=${utmSource}&utm_medium=originals&utm_campaign=wooahouse" class="wooa-tool-card" style="--wooa-color:${s.color}" target="_blank" rel="noopener">
          <span class="wooa-tool-icon">${s.icon}</span>
          <span class="wooa-tool-name">${s.name}</span>
          <span class="wooa-tool-title">${s.title}</span>
        </a>
      `).join('')}
    </div>
  `;

  // 광고 + 위젯을 하나의 컨테이너로 묶기
  const container = document.createElement('div');
  container.appendChild(adWrap);
  container.appendChild(wrap);

  const anchor = document.querySelector('.wooa-orig-anchor');
  if (anchor) anchor.replaceWith(container);
  else {
    const footer = document.querySelector('footer');
    if (footer) footer.before(container);
    else document.body.appendChild(container);
  }

  (window.adsbygoogle = window.adsbygoogle || []).push({});
})();
