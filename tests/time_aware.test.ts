import { describe, it, expect } from 'vitest';
import { TimeWeightConfig, TimeWeightCalculator } from '../src/temporal/time_aware';

describe('TimeWeightConfig', () => {
  it('defaults to exponential with 30-day half-life', () => {
    const cfg = new TimeWeightConfig();
    expect(cfg.decayType).toBe('exponential');
    expect(cfg.halfLifeDays).toBe(30);
    expect(cfg.maxAgeDays).toBe(365);
    expect(cfg.baseWeight).toBe(1);
    expect(cfg.minWeight).toBe(0.1);
  });

  it('accepts custom options', () => {
    const cfg = new TimeWeightConfig({
      decayType: 'linear',
      halfLifeDays: 15,
      baseWeight: 0.8,
    });
    expect(cfg.decayType).toBe('linear');
    expect(cfg.halfLifeDays).toBe(15);
    expect(cfg.baseWeight).toBe(0.8);
  });

  it('toDict returns expected keys', () => {
    const cfg = new TimeWeightConfig();
    const d = cfg.toDict();
    expect(d.decay_type).toBe('exponential');
    expect(d.half_life_days).toBe(30);
    expect(d.max_age_days).toBe(365);
  });
});

describe('TimeWeightCalculator', () => {
  const recentDate = new Date().toISOString();

  it('calculate with exponential decay returns max for recent', () => {
    const calc = new TimeWeightCalculator();
    const w = calc.calculate(recentDate);
    expect(w).toBeGreaterThan(0.9);
    expect(w).toBeLessThanOrEqual(1);
  });

  it('calculate with exponential decay returns low for old', () => {
    const calc = new TimeWeightCalculator();
    const oldDate = new Date(Date.now() - 400 * 86400000).toISOString();
    const w = calc.calculate(oldDate);
    expect(w).toBeLessThan(0.2);
    expect(w).toBeGreaterThanOrEqual(0.1);
  });

  it('calculate with linear decay', () => {
    const calc = new TimeWeightCalculator(new TimeWeightConfig({ decayType: 'linear', maxAgeDays: 100 }));
    const recent = calc.calculate(recentDate);
    expect(recent).toBeGreaterThan(0.9);
    const old = calc.calculate(new Date(Date.now() - 120 * 86400000).toISOString());
    expect(old).toBe(0.1);
  });

  it('calculate with step decay', () => {
    const calc = new TimeWeightCalculator(new TimeWeightConfig({
      decayType: 'step',
      recentWindowDays: 7,
      olderWindowDays: 90,
    }));
    const recent = calc.calculate(recentDate);
    expect(recent).toBe(1);
    const mid = calc.calculate(new Date(Date.now() - 30 * 86400000).toISOString());
    expect(mid).toBeCloseTo(0.5, 1);
    const old = calc.calculate(new Date(Date.now() - 200 * 86400000).toISOString());
    expect(old).toBe(0.1);
  });

  it('clamps weight to minWeight', () => {
    const calc = new TimeWeightCalculator(new TimeWeightConfig({ minWeight: 0.05, maxAgeDays: 10 }));
    const veryOld = calc.calculate(new Date(Date.now() - 500 * 86400000).toISOString());
    expect(veryOld).toBe(0.05);
  });

  it('applyWeights adds time_weight and sorts', () => {
    const calc = new TimeWeightCalculator();
    const mems = [
      { timestamp: new Date(Date.now() - 200 * 86400000).toISOString(), id: 'old' },
      { timestamp: recentDate, id: 'recent' },
    ];
    const result = calc.applyWeights(mems);
    expect(result[0].time_weight).toBeGreaterThan(result[1].time_weight as number);
    expect(result[0].id).toBe('recent');
  });

  it('applyWeights with custom field name', () => {
    const calc = new TimeWeightCalculator();
    const mems = [{ timestamp: recentDate }];
    const result = calc.applyWeights(mems, 'my_weight', false);
    expect(result[0].my_weight).toBeDefined();
  });

  it('getBestTimeRange detects explicit ranges', () => {
    const calc = new TimeWeightCalculator();
    expect(calc.getBestTimeRange('last 7 days')).toBeTruthy();
    expect(calc.getBestTimeRange('最近30天')).toBeTruthy();
  });

  it('getBestTimeRange detects keyword hints', () => {
    const calc = new TimeWeightCalculator();
    expect(calc.getBestTimeRange('today')).toBe('1d');
    expect(calc.getBestTimeRange('现在')).toBe('1d');
    expect(calc.getBestTimeRange('recent stuff')).toBe('7d');
    expect(calc.getBestTimeRange('最近的事情')).toBe('7d');
    expect(calc.getBestTimeRange('this month review')).toBe('30d');
  });

  it('getBestTimeRange returns null for no match', () => {
    const calc = new TimeWeightCalculator();
    expect(calc.getBestTimeRange('random query')).toBeNull();
  });

  it('handles invalid timestamp gracefully', () => {
    const calc = new TimeWeightCalculator();
    const w = calc.calculate('not-a-date');
    expect(w).toBe(0.1);
  });

  it('handles date-only format', () => {
    const calc = new TimeWeightCalculator();
    const w = calc.calculate('2026-06-01');
    expect(w).toBeGreaterThanOrEqual(0.1);
    expect(w).toBeLessThanOrEqual(1);
  });

  it('custom now parameter', () => {
    const calc = new TimeWeightCalculator(new TimeWeightConfig({ decayType: 'linear', maxAgeDays: 100 }));
    const future = new Date('2027-01-01T00:00:00Z');
    const w = calc.calculate('2026-01-01T00:00:00Z', future);
    expect(w).toBeGreaterThan(0);
  });
});
