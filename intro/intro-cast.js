/* 로그인 인트로 배치표(검수용). 시간은 모두 같은 시간축(초)입니다.
   차로차로는 이번 작업의 인트로 전용 동작(i_charo)을 씁니다.
   다른 친구들은 각자의 확정 동작을 그대로 쓰고 시간만 이 시간축에 맞춰 얹었습니다(파일은 고치지 않음). 티라는 6.7초 인트로 동작을 그대로 씁니다.
   place: [시각, 발 x, 발 y, 표시 키, 이징] — 논리 화면 1000×600 기준. 정렬 순서: 첨다니–티라–길통이–차로차로–도로덕 */
(function (global) {
  'use strict';
  var DUR = 6.7, LS = 0.55;                        // 최종 정렬 크기 = 대형 크기 × 0.55
  var ROW = 585, X = { chumdani: 295, tira: 387, giltong: 485, charocharo: 604, doroduck: 711 };   // 최종 폭(대형 키 × 0.55)과 14px 간격으로 계산
  function lineup(id, fx, fy, h, hEnd) {          // 5.35~6.05 함께 작아지며 아래 줄로 → 끝까지 유지
    return [[5.35, fx, fy, h, 'inout'], [6.05, X[id], ROW, hEnd == null ? h * LS : hEnd, 'inout'], [DUR, X[id], ROW, hEnd == null ? h * LS : hEnd, 'linear']];
  }
  var base = '../';
  var cast = [
    { id: 'chumdani', name: '첨다니', file: base + 'chumdani/chumdani.json', anchor: [200, 283], stageH: 167, z: 0, idle: 'c_idle',
      segs: [{ t0: 0, t1: 1.2, clip: 'c_run', rate: 2 }, { t0: 2.55, t1: 4.15, clip: 'c_welcome', rate: 2 }, { t0: 4.35, t1: 5.45, clip: 'c_flip', rate: 1.6 }],
      place: [[0, 790, 290, 125], [4.40, 790, 290, 125, 'linear'], [4.75, 520, 190, 125, 'out'], [5.10, 185, 520, 125, 'in']].concat(lineup('chumdani', 185, 520, 125)),
      reducedSegs: [], reducedPlace: [[0, 185, 520, 125]].concat(lineup('chumdani', 185, 520, 125)) },
    { id: 'giltong', name: '길통이', file: base + 'giltong/giltong.json', anchor: [200, 351], stageH: 285, z: 1, idle: 'g_idle',
      segs: [{ t0: 0, t1: 1.2, clip: 'g_run', rate: 2 }, { t0: 2.55, t1: 4.15, clip: 'g_welcome', rate: 2 }, { t0: 4.15, t1: 4.75, clip: 'g_finish', rate: 1 }],
      place: [[0, 485, 455, 210]].concat(lineup('giltong', 485, 455, 210)), reducedSegs: [] },
    { id: 'tira', name: '티라', file: base + 'tira_v3/tira_v3.json', anchor: [200, 382], stageH: 274, z: 2, idle: 't_idle', hold: true,
      segs: [{ t0: 0, t1: DUR, clip: 't_intro' }], reducedSegs: [{ t0: 0, t1: DUR, clip: 't_intro_r' }],
      // 티라 동작 안에 자체 정렬 축소(0.6배)가 있어 바깥 층은 키를 덜 줄임 → 최종 크기는 다른 친구와 같은 비율
      place: [[0, 330, 520, 175]].concat(lineup('tira', 330, 520, 175, 175 * LS / 0.6)) },
    { id: 'charocharo', name: '차로차로', file: base + 'charo-pet.json', anchor: [200, 370], stageH: 231, z: 0.5, idle: 'c_breath',
      segs: [{ t0: 0, t1: DUR, clip: 'i_charo' }], reducedSegs: [{ t0: 0, t1: DUR, clip: 'i_charo_r' }],
      // 다가오기(멀리서 작게 → 오른쪽 아래 환영 자리)는 바깥 층, 통통 튀기·점프는 동작(i_charo)
      place: [[0, 600, 385, 78], [1.15, 705, 528, 138, 'out']].concat(lineup('charocharo', 705, 528, 138)),
      reducedPlace: [[0, 705, 528, 138]].concat(lineup('charocharo', 705, 528, 138)) },
    { id: 'doroduck', name: '도로덕', file: base + 'doroduck/doroduck.json', anchor: [200, 354], stageH: 231, z: 4, idle: 'd_idle',
      segs: [{ t0: 0, t1: 1.2, clip: 'd_run', rate: 2 }, { t0: 2.55, t1: 4.15, clip: 'd_welcome', rate: 2 }, { t0: 4.15, t1: 4.75, clip: 'd_finish', rate: 1 }],
      place: [[0, 866, 500, 150]].concat(lineup('doroduck', 866, 500, 150)), reducedSegs: [] }
  ];
  var phases = [[0, '정면 우다다닥'], [1.2, '멈춤 · 티라 팻말 꺼내기'], [2.25, '차로차로 폴짝'], [2.55, '환영 슬로모션'], [4.15, '착지 · 첨다니 공중제비'], [5.35, '정렬 · 축소'], [6.05, '로그인 대기로']];
  global.CharoIntroCast = { duration: DUR, cast: cast, phases: phases, lineupRow: ROW, lineupX: X,
    welcome: { text: '환영합니다!', box: [260, 30, 740, 120] }, tv: [140, 20, 860, 560], slow: [2.55, 4.15] };
})(window);
