/**
 * wooa-footer.js (KO)
 * <footer class="footer"> 를 공용 WooaHouse 4컬럼 footer로 채웁니다.
 * EN 페이지는 wooa-footer-en.js 사용
 */
(function () {
  function init() {
    var t = document.querySelector('footer.footer');
    if (!t || t.children.length > 0) return; // 이미 채워진 경우 스킵
    var root = t.getAttribute('data-root') || '';
    t.innerHTML =
      '<div class="footer-inner">' +
        '<div class="footer-grid">' +
          '<div class="footer-col">' +
            '<h4>🏠 WooaHouse</h4>' +
            '<p style="color:#9CA3AF;font-size:.84rem;line-height:1.6">설치 불필요 &middot; 로그인 불필요<br>브라우저에서 바로 쓰는 무료 도구 모음</p>' +
            '<a href="https://wooahouse.com" target="_blank" style="margin-top:10px;display:inline-block;color:#10B981;">wooahouse.com →</a>' +
          '</div>' +
          '<div class="footer-col">' +
            '<h4>문서 &middot; 미디어</h4>' +
            '<a href="https://pdfkit.wooahouse.com" target="_blank">📄 WooaPDF</a>' +
            '<a href="https://imagekit.wooahouse.com" target="_blank">🖼️ WooaImage</a>' +
            '<a href="https://wooaocr.wooahouse.com" target="_blank">🔍 WooaOCR</a>' +
            '<a href="https://wooaaudio.wooahouse.com" target="_blank">🎵 WooaAudio</a>' +
            '<a href="https://wooavideo.wooahouse.com" target="_blank">📹 WooaVideo</a>' +
          '</div>' +
          '<div class="footer-col">' +
            '<h4>웹 &middot; 개발 &middot; 계산</h4>' +
            '<a href="https://colorkit.wooahouse.com" target="_blank">🎨 WooaColor</a>' +
            '<a href="https://textkit.wooahouse.com" target="_blank">📝 WooaText</a>' +
            '<a href="https://qrkit.wooahouse.com" target="_blank">🔲 WooaQR</a>' +
            '<a href="https://calckit.wooahouse.com" target="_blank">🧮 WooaCalc</a>' +
            '<a href="https://wooaviewer.wooahouse.com" target="_blank">👁️ WooaViewer</a>' +
            '<a href="https://wooasheet.wooahouse.com" target="_blank">📊 WooaSheet</a>' +
            '<a href="https://wooadev.wooahouse.com" target="_blank">🛠️ WooaDev</a>' +
          '</div>' +
          '<div class="footer-col">' +
            '<h4>정보</h4>' +
            '<a href="https://blog.wooahouse.com" target="_blank">✍️ 블로그</a>' +
            '<a href="' + root + 'about.html">서비스 소개</a>' +
            '<a href="' + root + 'privacy.html">개인정보처리방침</a>' +
          '</div>' +
        '</div>' +
        '<div class="footer-bottom">&copy; 2026 WooaHouse. All rights reserved.</div>' +
        '<div style="text-align:center;padding:8px 20px 0;font-size:.72rem;color:#4B5563;line-height:1.6">이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</div>' +
      '</div>';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
