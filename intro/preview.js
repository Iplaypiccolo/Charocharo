/* 검수 페이지 조작부. 임시 글자·배경은 이 파일에서만 그립니다(인트로 재생기에는 없음). */
(function () {
  'use strict';
  var C = window.CharoIntroCast, $ = function (id) { return document.getElementById(id); };
  var reduce = false; try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  $('tReduce').checked = reduce;
  var guide = true;
  function rr(ctx, x0, y0, x1, y1, r) { ctx.beginPath(); ctx.moveTo(x0 + r, y0); ctx.arcTo(x1, y0, x1, y1, r); ctx.arcTo(x1, y1, x0, y1, r); ctx.arcTo(x0, y1, x0, y0, r); ctx.arcTo(x0, y0, x1, y0, r); ctx.closePath(); }
  function fadeIn(T, a, b) { return T < a ? 0 : T > b ? 1 : (T - a) / (b - a); }
  var S = C.slow;
  var intro = CharoIntro.create({
    canvas: $('cv'), duration: C.duration, cast: C.cast, phases: C.phases, reduce: reduce,
    drawBack: function (ctx, T) {
      if (!guide) return;
      var a = Math.min(fadeIn(T, S[0], S[0] + 0.25), 1 - fadeIn(T, S[1] - 0.1, S[1] + 0.15));
      if (a > 0) { var t = C.tv; ctx.globalAlpha = 0.28 * a; ctx.fillStyle = '#e8f3ff'; rr(ctx, t[0], t[1], t[2], t[3], 70); ctx.fill(); ctx.globalAlpha = 1; }
    },
    drawFront: function (ctx, T) {
      if (!guide) return;
      var a = Math.min(fadeIn(T, S[0], S[0] + 0.2), 1 - fadeIn(T, S[1] - 0.1, S[1] + 0.15));
      if (a <= 0) return;
      var b = C.welcome.box; ctx.globalAlpha = a;
      ctx.setLineDash([6, 5]); ctx.strokeStyle = 'rgba(255,255,255,.7)'; ctx.lineWidth = 2; ctx.strokeRect(b[0], b[1], b[2] - b[0], b[3] - b[1]); ctx.setLineDash([]);
      ctx.fillStyle = '#fff'; ctx.font = '700 62px "Malgun Gothic","Noto Sans KR",sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(C.welcome.text, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 4);
      ctx.font = '500 13px sans-serif'; ctx.fillStyle = 'rgba(255,255,255,.75)'; ctx.fillText('임시 문구 위치', (b[0] + b[2]) / 2, b[3] + 14);
      ctx.globalAlpha = 1;
    },
    onError: function (e) { $('msg').innerHTML = '<span class="err">그림을 불러오지 못해 재생하지 않습니다: ' + String(e.message || e) + '</span>'; }
  });
  window.__intro = intro;
  intro.ready.then(function () { $('msg').textContent = '준비됨. 재생을 누르세요. 시점 막대를 움직이면 그 순간에서 멈춰 봅니다.'; }, function () {});
  $('bPlay').onclick = function () { intro.setReduce($('tReduce').checked); intro.start(); };
  $('bSkip').onclick = function () { intro.skip(); };
  $('tReduce').onchange = function () { intro.setReduce(this.checked); };
  $('tGuide').onchange = function () { guide = this.checked; };
  $('scrub').oninput = function () { intro.seek(+this.value); };
  var FACE = { '0,0,0': 'A 기본 미소', '3,3,1': 'B 신나서 질끈' };
  (function hud() {
    requestAnimationFrame(hud);
    var i = intro.info(), T = Math.min(i.T, C.duration), ch = i.last.charocharo;
    $('hT').textContent = (i.state === 'wait' ? '끝 · 대기 ' : '') + T.toFixed(2) + '초';
    $('hPh').textContent = i.state === 'wait' ? '로그인 대기' : intro.phase(T);
    if (ch) { var f = ch.fp; $('hFace').textContent = '차로차로 표정: ' + (FACE[[f.eyeL.img, f.browL.img, f.mouth.img].join(',')] || '?'); }
    if (i.state === 'play' && !i.paused) { $('scrub').value = T; } $('hS').textContent = (+$('scrub').value).toFixed(2);
  })();
})();
