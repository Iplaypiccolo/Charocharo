/*!
 * 로그인 인트로 보기 (viewer.js) — 고치는 화면이 아니라 '어떻게 움직이는지'를 보는 화면
 * 무대 + 재생 조절(느리게·한 프레임씩) + 시간표(장면·효과·캐릭터별 동작/이동) + 지금 상태 표 + 화면 위 표시(이름표·발 위치·지평선)
 * 필요: charo-pet.js, charo-intro.js, welcome-fx.js, intro-cast.js
 * 사용: CharoIntroViewer.mount(요소, { base: 'intro/', fxMeta, fxData, dataFor: function (id) { return 캐릭터 JSON 또는 null } })
 */
(function (global) {
  'use strict';
  var CSS = '' +
    '.iv{--iv-bg:#f4f6f8;--iv-card:#fff;--iv-ink:#13202e;--iv-sub:#5a6b7b;--iv-line:#dfe5ea;--iv-acc:#1f5f8f;--iv-slow:rgba(255,196,0,.16);' +
    'font:14px/1.5 "Pretendard",-apple-system,"Malgun Gothic","Noto Sans KR",sans-serif;color:var(--iv-ink);display:grid;gap:14px;padding:14px;box-sizing:border-box}' +
    '@media (prefers-color-scheme: dark){.iv{--iv-bg:#0f1a25;--iv-card:#162430;--iv-ink:#e3ebf2;--iv-sub:#9fb1c1;--iv-line:#2a3d4c;--iv-acc:#6fb0e0;--iv-slow:rgba(255,196,0,.12)}}' +
    '.iv *{box-sizing:border-box}.iv-top{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:14px;align-items:start}' +
    '@media (max-width:900px){.iv-top{grid-template-columns:1fr}}' +
    '.iv-stage{position:relative;width:100%;aspect-ratio:1000/600;border-radius:12px;overflow:hidden;background:linear-gradient(160deg,#1f5f8f,#10243a)}' +
    '.iv-stage canvas{position:absolute;inset:0;width:100%;height:100%;display:block}.iv-ov{pointer-events:none}' +
    '.iv-card{background:var(--iv-card);border:1px solid var(--iv-line);border-radius:12px;padding:12px}' +
    '.iv-card h3{margin:0 0 4px;font-size:13px;color:var(--iv-sub);font-weight:600;letter-spacing:.02em}' +
    '.iv-now{font-size:20px;font-weight:700;margin:0}.iv-desc{margin:6px 0 0;color:var(--iv-sub)}' +
    '.iv-t{font:600 28px/1 ui-monospace,Consolas,monospace}.iv-slowtag{display:inline-block;margin-left:8px;font-size:12px;font-weight:700;padding:2px 8px;border-radius:99px;background:#ffc400;color:#3a2a00;vertical-align:middle}' +
    '.iv-ctrl{display:flex;flex-wrap:wrap;gap:6px;align-items:center}' +
    '.iv button{font:inherit;font-size:13px;color:var(--iv-ink);background:var(--iv-card);border:1px solid var(--iv-line);border-radius:8px;padding:6px 10px;cursor:pointer}' +
    '.iv button:hover{border-color:var(--iv-acc)}.iv button[aria-pressed="true"],.iv button.main{background:var(--iv-acc);color:#fff;border-color:var(--iv-acc)}' +
    '.iv button:focus-visible{outline:2px solid var(--iv-acc);outline-offset:2px}.iv label{display:inline-flex;gap:5px;align-items:center;font-size:13px}' +
    '.iv-sep{width:1px;height:22px;background:var(--iv-line);margin:0 4px}' +
    '.iv-tbl{width:100%;border-collapse:collapse;font-size:12.5px}.iv-tbl td,.iv-tbl th{padding:5px 6px;border-bottom:1px solid var(--iv-line);text-align:left;vertical-align:top}' +
    '.iv-tbl th{color:var(--iv-sub);font-weight:600}.iv-tbl tr.sel td{background:rgba(31,95,143,.10)}.iv-tbl tr{cursor:pointer}.iv-num{font-family:ui-monospace,Consolas,monospace;white-space:nowrap}' +
    '.iv-tl{position:relative;user-select:none}.iv-row{display:grid;grid-template-columns:118px minmax(0,1fr);align-items:center;min-height:24px}' +
    '.iv-row .lab{font-size:12.5px;color:var(--iv-sub);padding-right:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.iv-row .lab b{color:var(--iv-ink)}' +
    '.iv-track{position:relative;height:22px;border-bottom:1px dashed var(--iv-line);cursor:pointer}' +
    '.iv-bar{position:absolute;top:2px;height:18px;border-radius:5px;font-size:11px;line-height:18px;padding:0 5px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.iv-bar.mv{background:transparent;border:1.5px solid currentColor;line-height:15px}' +
    '.iv-ruler{position:relative;height:18px;font:11px ui-monospace,Consolas,monospace;color:var(--iv-sub)}.iv-ruler span{position:absolute;transform:translateX(-50%)}' +
    '.iv-head{position:absolute;top:0;bottom:0;width:2px;background:#e5484d;pointer-events:none}.iv-slowband{position:absolute;top:0;bottom:0;background:var(--iv-slow);pointer-events:none}' +
    '.iv-hint{font-size:12.5px;color:var(--iv-sub);margin:0}';
  var COLORS = { chumdani: '#3d8bd8', giltong: '#e0603a', tira: '#a5743b', tarotaro: '#7fa800', charocharo: '#d9a400', doroduck: '#e08a00', fx: '#8a5cd6', phase: '#5f7486' };
  function el(tag, attrs, html) { var e = document.createElement(tag); for (var k in (attrs || {})) e.setAttribute(k, attrs[k]); if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function mount(root, opt) {
    var C = global.CharoIntroCast, CP = global.CharoPet, DUR = C.duration, SL = C.slow;
    if (!document.getElementById('iv-css')) { var st = el('style', { id: 'iv-css' }); st.textContent = CSS; document.head.appendChild(st); }
    root.innerHTML = '';
    var box = el('div', { class: 'iv' }); root.appendChild(box);
    box.innerHTML =
      '<div class="iv-top">' +
      ' <div style="display:grid;gap:10px"><div class="iv-stage"><canvas class="iv-cv" role="img" aria-label="로그인 인트로 무대"></canvas><canvas class="iv-ov" aria-hidden="true"></canvas></div>' +
      '  <div class="iv-ctrl">' +
      '   <button class="main" data-a="play">▶ 재생</button><button data-a="start" title="처음으로">⏮ 처음</button>' +
      '   <button data-a="back" title="한 프레임 뒤로 (←)">◀ 1프레임</button><button data-a="fwd" title="한 프레임 앞으로 (→)">1프레임 ▶</button><button data-a="end">끝으로 ⏭</button>' +
      '   <span class="iv-sep"></span><span class="iv-hint">속도</span>' +
      '   <button data-sp="1" aria-pressed="true">1×</button><button data-sp="0.5">0.5×</button><button data-sp="0.25">0.25×</button><button data-sp="0.1">0.1×</button>' +
      '   <span class="iv-sep"></span><label><input type="checkbox" data-o="loop" checked> 반복</label><label><input type="checkbox" data-o="reduce"> 모션 줄이기</label>' +
      '  </div>' +
      '  <div class="iv-ctrl"><span class="iv-hint">화면 표시</span>' +
      '   <label><input type="checkbox" data-o="labels" checked> 이름표·동작</label><label><input type="checkbox" data-o="feet"> 발 위치·앞뒤 순서</label><label><input type="checkbox" data-o="horizon"> 지평선·소실점</label>' +
      '   <span class="iv-sep"></span><span class="iv-hint">효과 층</span>' +
      '   <label><input type="checkbox" data-fx="bg" checked> 배경</label><label><input type="checkbox" data-fx="title" checked> 문구</label><label><input type="checkbox" data-fx="bursts" checked> 폭죽</label><label><input type="checkbox" data-fx="confetti" checked> 색종이</label>' +
      '  </div></div>' +
      ' <div style="display:grid;gap:10px">' +
      '  <div class="iv-card"><h3>지금</h3><div><span class="iv-t">0.00초</span><span class="iv-slowtag" hidden>슬로모션</span></div><p class="iv-now">-</p><p class="iv-desc"></p></div>' +
      '  <div class="iv-card"><h3>캐릭터 상태 (줄을 누르면 무대에 표시)</h3><table class="iv-tbl"><thead><tr><th>캐릭터</th><th>지금 동작</th><th>이동</th></tr></thead><tbody></tbody></table></div>' +
      ' </div>' +
      '</div>' +
      '<div class="iv-card"><h3>시간표 · 누르거나 끌면 그 시점으로 이동 · 노란 띠 = 슬로모션</h3><div class="iv-tl"></div>' +
      '<p class="iv-hint" style="margin-top:8px">채운 막대 = 캐릭터 동작(파일 안의 동작 이름), 테두리 막대 = 무대에서의 이동(원근 달리기·대형·자리 잡기·정렬). 이 화면은 보기 전용이에요. 동작을 고칠 때는 각 캐릭터 탭을 써요.</p></div>';
    var q = function (s) { return box.querySelector(s); }, qa = function (s) { return box.querySelectorAll(s); };
    var cv = q('.iv-cv'), ov = q('.iv-ov'), octx = ov.getContext('2d');
    C.cast.forEach(function (c) { if (opt.dataFor) { var d = opt.dataFor(c.id); if (d) c.data = d; } if (!c.data && opt.root != null) c.file = opt.root + c.file.replace(/^\.\.\//, ''); });
    var mobile = Math.min(screen.width, innerWidth) < 600;
    var fx = CharoWelcomeFX.create({ meta: opt.fxMeta, base: opt.base || '', data: opt.fxData, slow: SL, mobile: mobile });
    var intro = CharoIntro.create({ canvas: cv, duration: DUR, cast: C.cast, phases: C.phases, fx: fx,
      onError: function (e) { q('.iv-now').textContent = '불러오지 못했어요'; q('.iv-desc').textContent = String(e.message || e); } });
    var T = 0, playing = false, speed = 1, loop = true, reduce = false, sel = null, last = 0, show = { labels: true, feet: false, horizon: false };
    global.__ivIntro = intro;

    // ── 시간표 ──
    var tl = q('.iv-tl');
    function pct(t) { return (t / DUR * 100) + '%'; }
    function bar(track, t0, t1, text, color, cls) {
      var b = el('div', { class: 'iv-bar' + (cls ? ' ' + cls : ''), title: text + ' (' + t0.toFixed(2) + '~' + t1.toFixed(2) + '초)' }, esc(text));
      b.style.left = pct(t0); b.style.width = 'calc(' + ((t1 - t0) / DUR * 100) + '% - 2px)';
      if (cls === 'mv') b.style.color = color; else b.style.background = color;
      track.appendChild(b);
    }
    function row(label, color) { var r = el('div', { class: 'iv-row' }), lab = el('div', { class: 'lab' }, label), tr = el('div', { class: 'iv-track' }); r.appendChild(lab); r.appendChild(tr); tl.appendChild(r); return tr; }
    function buildTimeline() {
      tl.innerHTML = '';
      var ru = el('div', { class: 'iv-row' }); ru.appendChild(el('div', { class: 'lab' }, '')); var rr = el('div', { class: 'iv-ruler' });
      for (var t = 0; t <= DUR + 1e-9; t += 0.5) { var s = el('span', null, t.toFixed(1)); s.style.left = pct(t); rr.appendChild(s); }
      ru.appendChild(rr); tl.appendChild(ru);
      var tr = row('<b>장면</b>');
      C.phases.forEach(function (p, i) { var t1 = (C.phases[i + 1] || [DUR])[0]; bar(tr, p[0], t1, p[1], i % 2 ? '#7a8d9e' : COLORS.phase); });
      var fxt = fx.timeline();
      var tA = row('<b>효과</b> 배경·문구'), tB = row('폭죽 왼쪽'), tB2 = row('폭죽 오른쪽'), tCf = row('색종이');
      fxt.forEach(function (f) { var tgt = /폭죽 왼/.test(f[0]) ? tB : /폭죽 오/.test(f[0]) ? tB2 : /색종이/.test(f[0]) ? tCf : tA; bar(tgt, f[1], f[2], f[0], f[0] === '정리(사라짐)' ? '#b9a3e6' : COLORS.fx); });
      C.cast.forEach(function (c) {
        var col = COLORS[c.id] || '#888', names = {};
        (c.P ? c.P.clips : []).forEach(function (k) { names[k.id] = k.name; });
        var segs = (reduce && c.reducedSegs) ? c.reducedSegs : c.segs;
        var t1 = row('<b>' + esc(c.name) + '</b> 동작');
        if (!segs.length) bar(t1, 0, DUR, '대기 동작만', '#9aa7b2');
        segs.forEach(function (s) { bar(t1, s.t0, s.t1, (names[s.clip] || s.clip) + (s.rate && s.rate !== 1 ? ' · ' + (s.rate > 1 ? s.rate + '배 빠르게' : '') : ''), col); });
        if (c.steps) { var t3 = row('세부'); c.steps.forEach(function (m) { bar(t3, m[0], m[1], m[2], col, 'mv'); }); }
        var t2 = row('이동');
        (c.moves || []).forEach(function (m) { bar(t2, m[0], m[1], m[2], col, 'mv'); });
      });
      var band = el('div', { class: 'iv-slowband' }); band.style.left = 'calc(118px + (100% - 118px) * ' + (SL[0] / DUR) + ')'; band.style.width = 'calc((100% - 118px) * ' + ((SL[1] - SL[0]) / DUR) + ')'; tl.appendChild(band);
      head = el('div', { class: 'iv-head' }); tl.appendChild(head);
    }
    var head = null;
    function seekFromEvent(e) {
      var r = tl.getBoundingClientRect(), x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left - 118;
      var w = r.width - 118; if (w <= 0) return; T = Math.max(0, Math.min(DUR, x / w * DUR)); playing = false; syncPlay();
    }
    var dragging = false;
    tl.addEventListener('pointerdown', function (e) { dragging = true; tl.setPointerCapture(e.pointerId); seekFromEvent(e); });
    tl.addEventListener('pointermove', function (e) { if (dragging) seekFromEvent(e); });
    tl.addEventListener('pointerup', function () { dragging = false; });

    // ── 조작 ──
    function syncPlay() { var b = q('[data-a="play"]'); b.textContent = playing ? '❚❚ 멈춤' : '▶ 재생'; }
    box.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var a = b.getAttribute('data-a'), sp = b.getAttribute('data-sp');
      if (a === 'play') { if (!playing && T >= DUR - 1e-6) T = 0; playing = !playing; syncPlay(); }
      if (a === 'start') { T = 0; }
      if (a === 'end') { T = DUR; playing = false; syncPlay(); }
      if (a === 'back' || a === 'fwd') { playing = false; syncPlay(); T = Math.max(0, Math.min(DUR, T + (a === 'fwd' ? 1 : -1) / 30)); }
      if (sp) { speed = +sp; Array.prototype.forEach.call(qa('[data-sp]'), function (x) { x.setAttribute('aria-pressed', String(x === b)); }); }
    });
    box.addEventListener('change', function (e) {
      var i = e.target, o = i.getAttribute('data-o'), f = i.getAttribute('data-fx');
      if (o === 'loop') loop = i.checked;
      if (o === 'reduce') { reduce = i.checked; intro.setReduce(reduce); buildTimeline(); }
      if (o && show.hasOwnProperty(o)) show[o] = i.checked;
      if (f) fx.layers[f] = i.checked;
    });
    document.addEventListener('keydown', function (e) {
      if (!box.isConnected || /INPUT|TEXTAREA|SELECT/.test((e.target.tagName || ''))) return;
      if (e.code === 'Space') { e.preventDefault(); q('[data-a="play"]').click(); }
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); q(e.key === 'ArrowRight' ? '[data-a="fwd"]' : '[data-a="back"]').click(); }
    });
    var tbody = q('.iv-tbl tbody');
    tbody.addEventListener('click', function (e) { var tr = e.target.closest('tr'); if (!tr) return; sel = sel === tr.dataset.id ? null : tr.dataset.id; });

    function curSeg(c, t) { var segs = (reduce && c.reducedSegs) ? c.reducedSegs : c.segs, s = null; segs.forEach(function (x) { if (t >= x.t0 - 1e-9 && t <= x.t1 + 1e-9) s = x; }); return s; }
    function curStep(c, t) { var m = null; (c.steps || []).forEach(function (x) { if (t >= x[0] && t <= x[1]) m = x; }); return m; }
    function curMove(c, t) { var m = null; (c.moves || []).forEach(function (x) { if (t >= x[0] && t <= x[1]) m = x; }); return m; }
    function placeOf(c) { return (reduce && c.reducedPlace) ? c.reducedPlace : c.place; }

    function drawOverlay() {
      var r = ov.getBoundingClientRect(), dpr = global.devicePixelRatio || 1, w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
      if (ov.width !== w || ov.height !== h) { ov.width = w; ov.height = h; }
      var s = Math.min(w / 1000, h / 600);
      octx.setTransform(1, 0, 0, 1, 0, 0); octx.clearRect(0, 0, w, h); octx.setTransform(s, 0, 0, s, 0, 0);
      if (show.horizon) {
        var vp = C.vanishingPoint; octx.strokeStyle = 'rgba(255,255,255,.55)'; octx.setLineDash([6, 6]); octx.lineWidth = 1.5 / s * dpr;
        octx.beginPath(); octx.moveTo(0, vp[1]); octx.lineTo(1000, vp[1]); octx.stroke(); octx.setLineDash([]);
        octx.fillStyle = '#ff5d5d'; octx.beginPath(); octx.arc(vp[0], vp[1], 5, 0, 7); octx.fill();
        octx.fillStyle = '#fff'; octx.font = '600 13px sans-serif'; octx.fillText('소실점 · 지평선', vp[0] + 9, vp[1] - 7);
      }
      var order = (intro.info().last.__order || []);
      C.cast.forEach(function (c) {
        if (!c.P) return;
        var pl = CharoIntro.samplePlace(placeOf(c), Math.min(T, DUR)); if (!(pl[3] > 6)) return;
        var x = pl[1], y = pl[2], hh = pl[3], col = COLORS[c.id] || '#fff';
        if (sel === c.id) { octx.strokeStyle = col; octx.lineWidth = 3; octx.beginPath(); octx.ellipse(x, y - hh * 0.5, hh * 0.55, hh * 0.62, 0, 0, 7); octx.stroke(); }
        if (show.feet) {
          octx.fillStyle = col; octx.beginPath(); octx.arc(x, y, 4, 0, 7); octx.fill();
          octx.fillStyle = '#fff'; octx.font = '700 12px sans-serif'; octx.fillText('앞뒤 ' + (order.indexOf(c.id) + 1), x + 7, y + 4);
        }
        if (show.labels && hh > 30) {
          var sg = curSeg(c, T), nm = sg ? ((c.P.clips.filter(function (k) { return k.id === sg.clip; })[0] || {}).name || sg.clip) : '대기';
          var stp = curStep(c, T); if (stp) nm = stp[2]; else if (/^인트로 \(/.test(nm)) nm = '대기';
          nm = nm.replace(/^인트로\s*/, '').replace(/\s*\(.*\)$/, '');
          var txt = c.name + ' · ' + nm; octx.font = '600 12px sans-serif'; var tw = octx.measureText(txt).width + 12, ly = y - hh - 12;
          octx.fillStyle = 'rgba(16,32,46,.82)'; octx.beginPath(); octx.roundRect ? octx.roundRect(x - tw / 2, ly - 15, tw, 20, 6) : octx.rect(x - tw / 2, ly - 15, tw, 20); octx.fill();
          octx.fillStyle = col; octx.fillRect(x - tw / 2, ly - 15, 4, 20); octx.fillStyle = '#fff'; octx.fillText(txt, x - tw / 2 + 8, ly);
        }
      });
    }
    function updatePanel() {
      q('.iv-t').textContent = T.toFixed(2) + '초';
      q('.iv-slowtag').hidden = !(T >= SL[0] && T <= SL[1]);
      var ph = C.phases[0]; C.phases.forEach(function (p) { if (T >= p[0]) ph = p; });
      q('.iv-now').textContent = ph[1]; q('.iv-desc').textContent = ph[2] || '';
      var rows = C.cast.map(function (c) {
        var sg = curSeg(c, T), mv = curMove(c, T), nm = '대기 동작';
        if (sg && c.P) { var k = c.P.clips.filter(function (x) { return x.id === sg.clip; })[0]; var stp = curStep(c, T); nm = (k ? k.name.replace(/\s*\(.*\)$/, '') : sg.clip) + (stp ? ' → <b>' + esc(stp[2]) + '</b>' : '') + ' <span class="iv-num">' + ((sg.from || 0) + (T - sg.t0) * (sg.rate || 1)).toFixed(2) + '초</span>'; }
        return '<tr data-id="' + c.id + '"' + (sel === c.id ? ' class="sel"' : '') + '><td><b style="color:' + (COLORS[c.id] || '') + '">●</b> ' + esc(c.name) + '</td><td>' + nm + '</td><td>' + esc(mv ? mv[2] : '-') + '</td></tr>';
      }).join('');
      if (tbody.__last !== rows) { tbody.innerHTML = rows; tbody.__last = rows; }
      if (head) head.style.left = 'calc(118px + (100% - 118px) * ' + (T / DUR) + ')';
    }
    function frame(now) {
      requestAnimationFrame(frame);
      var dt = last ? Math.min(0.1, (now - last) / 1000) : 0; last = now;
      if (playing) { T += dt * speed; if (T >= DUR) { if (loop) T = 0; else { T = DUR; playing = false; syncPlay(); } } }
      intro.seek(T); drawOverlay(); updatePanel();
    }
    intro.ready.then(function () { buildTimeline(); requestAnimationFrame(frame); }, function () {});
    return { intro: intro, fx: fx, seek: function (t) { T = t; }, state: function () { return { T: T, playing: playing, speed: speed }; } };
  }
  global.CharoIntroViewer = { mount: mount };
})(window);
