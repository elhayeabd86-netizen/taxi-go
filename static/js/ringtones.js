/**
 * Sonneries synthétisées (Web Audio) — une clé = un motif différent.
 * Réutilisable : playRingtone('classic'), playRingtoneFromSelect(element)
 */
(function () {
  function getCtx() {
    var Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    return new Ctx();
  }

  function beep(ctx, start, freq, duration, type, gain) {
    var osc = ctx.createOscillator();
    var g = ctx.createGain();
    osc.type = type || 'sine';
    osc.frequency.setValueAtTime(freq, start);
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(gain || 0.12, start + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    osc.connect(g);
    g.connect(ctx.destination);
    osc.start(start);
    osc.stop(start + duration + 0.05);
  }

  function runPattern(ctx, pattern) {
    var t = ctx.currentTime + 0.05;
    pattern.forEach(function (step) {
      beep(ctx, t, step.f, step.d, step.wave, step.vol);
      t += step.gap != null ? step.gap : step.d;
    });
  }

  var patterns = {
    classic: [
      { f: 523.25, d: 0.12, gap: 0.14, wave: 'sine', vol: 0.14 },
      { f: 659.25, d: 0.12, gap: 0.14, wave: 'sine', vol: 0.14 },
      { f: 783.99, d: 0.22, gap: 0.2, wave: 'sine', vol: 0.15 },
    ],
    bell: [
      { f: 880, d: 0.08, gap: 0.1, wave: 'sine', vol: 0.18 },
      { f: 1174.66, d: 0.15, gap: 0.18, wave: 'sine', vol: 0.16 },
      { f: 880, d: 0.1, gap: 0.12, wave: 'sine', vol: 0.14 },
    ],
    digital: [
      { f: 1200, d: 0.05, gap: 0.07, wave: 'square', vol: 0.06 },
      { f: 800, d: 0.05, gap: 0.07, wave: 'square', vol: 0.06 },
      { f: 1200, d: 0.05, gap: 0.07, wave: 'square', vol: 0.06 },
      { f: 800, d: 0.05, gap: 0.07, wave: 'square', vol: 0.06 },
    ],
    soft: [
      { f: 440, d: 0.25, gap: 0.28, wave: 'sine', vol: 0.08 },
      { f: 554.37, d: 0.25, gap: 0.28, wave: 'sine', vol: 0.07 },
    ],
    urgent: [
      { f: 1000, d: 0.08, gap: 0.1, wave: 'triangle', vol: 0.14 },
      { f: 1000, d: 0.08, gap: 0.1, wave: 'triangle', vol: 0.14 },
      { f: 1000, d: 0.08, gap: 0.1, wave: 'triangle', vol: 0.14 },
      { f: 1500, d: 0.15, gap: 0.2, wave: 'triangle', vol: 0.15 },
    ],
    melody: [
      { f: 392, d: 0.15, gap: 0.05, wave: 'sine', vol: 0.12 },
      { f: 440, d: 0.15, gap: 0.05, wave: 'sine', vol: 0.12 },
      { f: 493.88, d: 0.15, gap: 0.05, wave: 'sine', vol: 0.12 },
      { f: 523.25, d: 0.28, gap: 0.2, wave: 'sine', vol: 0.13 },
    ],
  };

  window.playRingtone = function (key) {
    var k = key && patterns[key] ? key : 'classic';
    var ctx = getCtx();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();
    runPattern(ctx, patterns[k]);
  };

  window.playRingtoneFromSelect = function (selectEl) {
    if (!selectEl || !selectEl.value) window.playRingtone('classic');
    else window.playRingtone(selectEl.value);
  };
})();
