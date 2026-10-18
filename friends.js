/* 친구들 탭: 캐릭터마다 캐릭터 파일을 읽어 미리보기 무대에서 동작을 재생합니다.
   고칠 때는 '에디터에서 고치기'로 같은 캐릭터 탭의 모션 에디터를 엽니다. */
(function () {
  'use strict';
  var CHARS = [
    { id: 'charocharo', name: '차로차로', file: 'charo-pet.json', review: null, note: '마우스·클릭·타자·시간에 반응하는 메인 캐릭터' },
    { id: 'chumdani', name: '첨다니', file: 'chumdani/chumdani.json', review: 'chumdani/review.html', note: '와이파이 감정 신호 · 공중제비' },
    { id: 'tira', name: '티라', file: 'tira_v3/tira_v3.json', review: 'tira_v3/review.html', note: "팔 없이 입으로 문 거꾸로 '환영' 팻말 · 불뿜기 (v3)" },
    { id: 'giltong', name: '길통이', file: 'giltong/giltong.json', review: 'giltong/review.html', note: '한 발 들고 인사' },
    { id: 'doroduck', name: '도로덕', file: 'doroduck/doroduck.json', review: 'doroduck/review.html', note: "'합니다!' 팻말" },
    { id: 'tarotaro', name: '타로타로', file: 'tarotaro/tarotaro.json', review: null, note: '불 보고 움찔 → 점프·환영 → 한쪽씩 착지 → 엣헴 (로그인 인트로 포함)' }
  ];
  function $(id) { return document.getElementById(id); }
  function start() {
    var CP = window.CharoPet; if (!CP || !CP.Engine) return setTimeout(start, 100);
    var tabs = $('fTabs'), cv = $('fCv'), ctx = cv.getContext('2d'), btns = $('fBtns'), cur = null, eng = null, P = null, raf = 0, cache = {};
    var reduce = false; try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
    tabs.innerHTML = CHARS.map(function (c) { return '<button type="button" role="tab" id="ft_' + c.id + '" data-id="' + c.id + '">' + c.name + '</button>'; }).join('');
    tabs.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) pick(b.dataset.id); });
    function size() {
      var w = Math.min(360, cv.parentNode.clientWidth - 2), dpr = devicePixelRatio || 1;
      cv.style.width = w + 'px'; cv.style.height = w + 'px'; cv.width = Math.round(w * dpr); cv.height = Math.round(w * dpr);
    }
    addEventListener('resize', size);
    function pick(id) {
      var c = CHARS.filter(function (x) { return x.id === id; })[0] || CHARS[0]; cur = c;
      Array.prototype.forEach.call(tabs.children, function (b) { b.setAttribute('aria-selected', String(b.dataset.id === id)); });
      try { localStorage.setItem('charoFriendsTab', id); } catch (e) {}
      $('fName').textContent = c.name; $('fNote').textContent = c.note;
      $('fEdit').href = 'editor.html#' + c.id;
      $('fReview').hidden = !c.review; if (c.review) $('fReview').href = c.review;
      $('fFile').textContent = c.file;
      btns.innerHTML = '<span class="hint">불러오는 중…</span>';
      (cache[id] ? Promise.resolve(cache[id]) : fetch(c.file, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw 0; return r.json(); }))
        .then(function (p) { cache[id] = p; return CP.preload(p).then(function () { return p; }); })
        .then(function (p) {
          if (cur !== c) return;
          P = p; eng = new CP.Engine(P, { reduce: reduce });
          var list = (P.preview && P.preview.length) ? P.preview : P.clips.filter(function (k) { return !k.loop; }).map(function (k) { return { label: k.name, clip: k.id }; });
          btns.innerHTML = list.map(function (v) { return '<button type="button" data-clip="' + v.clip + '"' + (v.extra ? ' class="extra"' : '') + '>' + v.label + '</button>'; }).join('');
          size(); if (!raf) raf = requestAnimationFrame(loop);
        })
        .catch(function () { if (cur === c) btns.innerHTML = '<span class="hint">캐릭터 파일을 불러오지 못했어요.</span>'; });
    }
    btns.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b && eng) { var id = b.dataset.clip; if (reduce && P.reducedClip && P.reducedClip[id]) id = P.reducedClip[id]; eng.play(id); } });   // 모션 줄이기: 캐릭터가 따로 준비한 버전이 있으면 그것으로
    cv.addEventListener('pointermove', function (e) { if (!eng) return; var r = cv.getBoundingClientRect(); eng.pointer(e.clientX - r.left - r.width / 2, e.clientY - r.top - r.height / 2, r.width / 400); });
    function loop(t) {
      raf = requestAnimationFrame(loop);
      if (!eng || document.hidden) return;
      var off = eng.update(t), fp = CP.finalPose(P, off, eng.follow), sc = cv.width / 400;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
      CP.render(ctx, P, fp, CP.worldMatrices(P, fp), [sc, 0, 0, sc, 0, 0]);
    }
    var first = (location.hash || '').replace('#', ''); if (!CHARS.some(function (c) { return c.id === first; })) { try { first = localStorage.getItem('charoFriendsTab'); } catch (e) { first = null; } }
    pick(first || 'charocharo');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
