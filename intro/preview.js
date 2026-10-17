/* 검수 페이지 조작부. 효과(배경·문구·폭죽·색종이)는 welcome-fx.js, 캐릭터는 charo-intro.js가 같은 시간축으로 그림. */
(function () {
  'use strict';
  var C = window.CharoIntroCast, $ = function (id) { return document.getElementById(id); };
  var reduce = false; try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  $('tReduce').checked = reduce;
  var mobile = Math.min(screen.width, innerWidth) < 600;
  var metaP = window.__FXMETA ? Promise.resolve(window.__FXMETA) : fetch('assets/fx-assets.json').then(function (r) { return r.json(); });
  var intro = null;
  metaP.then(function (meta) {
    var fx = CharoWelcomeFX.create({ meta: meta, base: '', data: window.__FXDATA, slow: C.slow, reduce: reduce, mobile: mobile });
    intro = CharoIntro.create({
      canvas: $('cv'), duration: C.duration, cast: C.cast, phases: C.phases, reduce: reduce, fx: fx,
      onWelcome: function () { $('sr').textContent = '환영합니다!'; },     // 화면 낭독기에는 문구를 한 번만 알림(장식 입자는 읽지 않음)
      onError: function (e) { $('msg').innerHTML = '<span class="err">그림을 불러오지 못해 재생하지 않습니다: ' + String(e.message || e) + '</span>'; }
    });
    window.__intro = intro; window.__fx = fx;
    intro.ready.then(function () { $('msg').textContent = '준비됨. 재생을 누르세요. 시점 막대를 움직이면 그 순간에서 멈춰 봅니다.' + (fx.failed.length ? ' (불러오지 못한 효과: ' + fx.failed.join(', ') + ')' : ''); }, function () {});
    hook();
  });
  function hook() {
  $('bPlay').onclick = function () { $('sr').textContent = ''; intro.setReduce($('tReduce').checked); intro.start(); };
  $('bSkip').onclick = function () { intro.skip(); };
  $('tReduce').onchange = function () { intro.setReduce(this.checked); };
  $('scrub').oninput = function () { intro.seek(+this.value); };
  var FACE = null;
  function faces() { if (FACE) return FACE; var ch = C.cast.filter(function (c) { return c.id === 'charocharo'; })[0]; if (!ch || !ch.P) return {}; FACE = {}; ch.P.faces.forEach(function (f) { if (f.id === 'f00') FACE[[f.img.eyeL, f.img.browL, f.img.mouth].join(',')] = 'A 기본 미소'; if (f.id === 'f22') FACE[[f.img.eyeL, f.img.browL, f.img.mouth].join(',')] = 'B 신나서 질끈'; }); return FACE; }   // 표정 번호는 데이터에서
  (function hud() {
    requestAnimationFrame(hud);
    var i = intro.info(), T = Math.min(i.T, C.duration), ch = i.last.charocharo;
    $('hT').textContent = (i.state === 'wait' ? '끝 · 대기 ' : '') + T.toFixed(2) + '초';
    $('hPh').textContent = i.state === 'wait' ? '로그인 대기' : intro.phase(T);
    if (ch) { var f = ch.fp; $('hFace').textContent = '차로차로 표정: ' + (faces()[[f.eyeL.img, f.browL.img, f.mouth.img].join(',')] || '?'); }
    if (i.state === 'play' && !i.paused) { $('scrub').value = T; } $('hS').textContent = (+$('scrub').value).toFixed(2);
  })();
  }
})();
