/* 로그인 인트로 배치표 (2026-10-17 개정 콘티). 시간은 모두 같은 시간축(초)입니다.
   0.00     티라만 서 있음(친구들은 아직 안 보임)
   0.30~    길통이·첨다니·차로차로·도로덕이 지평선의 한 점(소실점)에서 나와 같은 땅 위를 달려오며 커짐(원근)
   0.30~2.30 티라: 불 뿜기 → 뜨거워 → '아 맞다' → 머리만 돌려 입으로 거꾸로 팻말 꺼냄
   1.55     첨다니가 먼저 도착 → 1.62 고무공 점프 → 차로차로 위쪽(뒤)에 자리
   2.30~3.90 친구들이 도착하는 그 순간 슬로모션: '환영합니다!' 문구·배경·폭죽·색종이(welcome-fx.js)
   3.90~    착지·균형 회복 → 4.20 첨다니가 공중제비로 티라 왼쪽으로
   5.15~5.85 함께 작아지며 아래 줄로: 첨다니–티라–길통이–차로차로–도로덕 → 로그인 대기
   place 키: [시각, 발 x, 발 y, 표시 키, 이징, 앞뒤(클수록 앞)] — 논리 화면 1000×600 */
(function (global) {
  'use strict';
  var DUR = 6.3, SLOW = [2.30, 3.90], LS = 0.55, L0 = 5.15, L1 = 5.85;
  var VP = [500, 336];                      // 소실점 = 겨울 배경 그림의 도로가 모이는 점(배경을 무대 폭에 맞춰 그렸을 때)
  var ROW = 585, X = { chumdani: 300, tira: 393, giltong: 490, charocharo: 602, doroduck: 705 };   // 최종 폭(대형 키×0.55) + 14px 간격
  var F = { tira: [300, 525, 175], giltong: [470, 505, 205], charocharo: [690, 528, 138], doroduck: [865, 505, 150],
            chumLane: [600, 520, 125], chumPerch: [736, 405, 120], chumSide: [150, 522, 125] };
  // 원근 달리기: 지평선의 점(배율 s0)에서 제자리(배율 1)까지. 배율은 지수적으로 커짐(일정한 속도로 다가올 때처럼)
  function run(f, t0, t1, s0, drift) {
    var k = [[0, VP[0], VP[1], 0, 'linear', 0], [t0 - 0.001, VP[0], VP[1], 0, 'linear', 0]];
    for (var t = t0; t <= t1 + 1e-9; t = Math.round((t + 0.05) * 1000) / 1000) {
      var u = Math.min(1, (t - t0) / (t1 - t0)), s = Math.exp(Math.log(s0) * (1 - u));
      k.push([t, VP[0] + (f[0] - VP[0]) * s, VP[1] + (f[1] - VP[1]) * s, f[2] * s, 'linear', s]);
    }
    if (drift) {   // 슬로모션 동안 아주 조금 더 앞으로 밀려옴(멈춰 서지 않은 느낌)
      var d = drift; k.push([SLOW[1], VP[0] + (f[0] - VP[0]) * d, VP[1] + (f[1] - VP[1]) * d, f[2] * d, 'out', d]);
      k.push([4.30, f[0], f[1], f[2], 'inout', 1]);
    }
    return k;
  }
  function lineup(id, f, hEnd, dep) {
    var h = hEnd == null ? f[2] * LS : hEnd;
    return [[L0, f[0], f[1], f[2], 'inout', dep], [L1, X[id], ROW, h, 'inout', dep], [DUR, X[id], ROW, h, 'linear', dep]];
  }
  // 첨다니: 0.30 출발 → 1.55 먼저 도착(자기 줄: 길통이와 차로차로 사이) → 1.62 점프 시작(납작) → 1.86~2.16 공중 → 차로차로 위쪽(뒤)
  var cl = F.chumLane, cp = F.chumPerch, cs = F.chumSide;
  var chum = run(cl, 0.30, 1.55, 0.03).concat([[1.84, cl[0], cl[1], cl[2], 'linear', 1]]);
  for (var i = 1; i <= 6; i++) {           // 포물선(위로 높이 솟았다 차로차로 뒤쪽 자리에 내려앉음)
    var u = i / 6, x = cl[0] + (cp[0] - cl[0]) * u, y = cl[1] + (cp[1] - cl[1]) * u - 4 * 150 * u * (1 - u);
    chum.push([1.86 + 0.30 * u, x, y, cl[2] + (cp[2] - cl[2]) * u, 'linear', u < 1 ? 1 : 0.4]);
  }
  chum.push([4.30, cp[0], cp[1], cp[2], 'linear', 0.4]);
  // 4.30~4.98 공중제비로 친구들 머리 위를 넘어 티라 왼쪽에 착지
  for (var j = 1; j <= 8; j++) {
    var v = j / 8, x2 = cp[0] + (cs[0] - cp[0]) * v, y2 = cp[1] + (cs[1] - cp[1]) * v - 4 * 240 * v * (1 - v);   // 티라 머리 위로 충분히 높게
    chum.push([4.30 + 0.68 * v, x2, y2, cp[2] + (cs[2] - cp[2]) * v, 'linear', 2]);
  }
  chum = chum.concat(lineup('chumdani', cs, null, 0.3));
  var base = '../';
  var cast = [
    { id: 'chumdani', name: '첨다니', file: base + 'chumdani/chumdani.json', anchor: [200, 283], stageH: 167, idle: 'c_idle',
      segs: [{ t0: 0.30, t1: 1.62, clip: 'c_run_i', rate: 1.3 }, { t0: 1.62, t1: 2.42, clip: 'c_jump_i' }, { t0: SLOW[0], t1: SLOW[1], clip: 'c_welcome', rate: 2 },
             { t0: 4.22, t1: 5.32, clip: 'c_flip', rate: 1.6 }],
      place: chum, reducedSegs: [],
      reducedPlace: [[0, cp[0], cp[1], cp[2], 'linear', 0.4], [4.30, cp[0], cp[1], cp[2], 'linear', 0.4], [4.98, cs[0], cs[1], cs[2], 'inout', 0.3]].concat(lineup('chumdani', cs, null, 0.3)) },
    { id: 'giltong', name: '길통이', file: base + 'giltong/giltong.json', anchor: [200, 351], stageH: 285, idle: 'g_idle',
      segs: [{ t0: 0.30, t1: SLOW[0], clip: 'g_run_i' }, { t0: SLOW[0], t1: SLOW[1], clip: 'g_welcome', rate: 2 }, { t0: SLOW[1], t1: 4.50, clip: 'g_finish', rate: 1 }],
      place: run(F.giltong, 0.30, SLOW[0], 0.03, 1.02).concat(lineup('giltong', F.giltong, null, 0.9)), reducedSegs: [],
      reducedPlace: [[0].concat(F.giltong, ['linear', 0.9])].concat(lineup('giltong', F.giltong, null, 0.9)) },
    { id: 'tira', name: '티라', file: base + 'tira_v3/tira_v3.json', anchor: [200, 382], stageH: 274, idle: 't_idle', hold: true,
      segs: [{ t0: 0, t1: DUR, clip: 't_intro' }], reducedSegs: [{ t0: 0, t1: DUR, clip: 't_intro_r' }],
      place: [[0].concat(F.tira, ['linear', 0.95])].concat(lineup('tira', F.tira, null, 0.95)) },
    { id: 'charocharo', name: '차로차로', file: base + 'charo-pet.json', anchor: [200, 370], stageH: 231, idle: 'c_breath',
      segs: [{ t0: 0, t1: DUR, clip: 'i_charo' }], reducedSegs: [{ t0: 0, t1: DUR, clip: 'i_charo_r' }],
      place: run(F.charocharo, 0.30, SLOW[0], 0.03, 1.02).concat(lineup('charocharo', F.charocharo, null, 1)),
      reducedPlace: [[0].concat(F.charocharo, ['linear', 1])].concat(lineup('charocharo', F.charocharo, null, 1)) },
    { id: 'doroduck', name: '도로덕', file: base + 'doroduck/doroduck.json', anchor: [200, 354], stageH: 231, idle: 'd_idle',
      segs: [{ t0: 0.30, t1: SLOW[0], clip: 'd_run_i' }, { t0: SLOW[0], t1: SLOW[1], clip: 'd_welcome', rate: 2 }, { t0: SLOW[1], t1: 4.75, clip: 'd_finish_i', rate: 1 }],
      place: run(F.doroduck, 0.30, SLOW[0], 0.03, 1.02).concat(lineup('doroduck', F.doroduck, null, 0.92)), reducedSegs: [],
      reducedPlace: [[0].concat(F.doroduck, ['linear', 0.92])].concat(lineup('doroduck', F.doroduck, null, 0.92)) }
  ];
  var phases = [[0, '티라 혼자 · 친구들 출발 전'], [0.3, '친구들 달려옴 · 티라 불 뿜기'], [1.2, '티라 팻말 꺼내기'], [1.62, '첨다니 고무공 점프'],
                [2.12, '차로차로 폴짝'], [2.3, '환영 슬로모션'], [3.9, '착지'], [4.3, '첨다니 공중제비 → 티라 옆'], [5.15, '정렬 · 축소'], [5.85, '로그인 대기로']];
  global.CharoIntroCast = { duration: DUR, cast: cast, phases: phases, lineupRow: ROW, lineupX: X, slow: SLOW, vanishingPoint: VP, formation: F };
})(window);
