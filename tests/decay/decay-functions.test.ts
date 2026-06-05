import { describe, it, expect } from 'vitest';
import {
  exponentialDecay,
  calculateWeight,
  halfLifeToDays,
  HALF_LIFE,
  LAMBDA,
  DEFAULT_DECAY_CONFIG,
} from '../../src/decay/functions';

describe('Decay Functions', () => {
  it('exponentialDecay returns base when daysElapsed <= 0', () => {
    expect(exponentialDecay(1.0, 0, 30)).toBe(1.0);
    expect(exponentialDecay(1.0, -1, 30)).toBe(1.0);
  });

  it('exponentialDecay returns 0 when halfLifeDays <= 0', () => {
    expect(exponentialDecay(1.0, 10, 0)).toBe(0);
    expect(exponentialDecay(1.0, 10, -5)).toBe(0);
  });

  it('exponentialDecay decays with half-life', () => {
    const w = exponentialDecay(1.0, 30, 30);
    expect(w).toBeCloseTo(0.5, 1);
    const w2 = exponentialDecay(1.0, 60, 30);
    expect(w2).toBeCloseTo(0.25, 1);
  });

  it('calculateWeight uses category half-life', () => {
    const w = calculateWeight(1.0, 7, 'episodic');
    expect(w).toBeLessThan(1);
    expect(w).toBeGreaterThan(0);
  });

  it('calculateWeight falls back to 30 days for unknown category', () => {
    const w = calculateWeight(1.0, 30, 'unknown');
    expect(w).toBeCloseTo(0.5, 1);
  });

  it('halfLifeToDays computes correct half-life', () => {
    const hl = halfLifeToDays(0.5, 1.0, 30);
    expect(hl).toBeCloseTo(30, 0);
  });

  it('halfLifeToDays returns 30 for invalid inputs', () => {
    expect(halfLifeToDays(1.5, 1.0, 30)).toBe(30);
    expect(halfLifeToDays(0, 1.0, 30)).toBe(30);
    expect(halfLifeToDays(0.5, 1.0, 0)).toBe(30);
  });

  it('HALF_LIFE has all expected categories', () => {
    expect(HALF_LIFE.episodic).toBe(7);
    expect(HALF_LIFE.semantic).toBe(90);
    expect(HALF_LIFE.procedural).toBe(180);
  });

  it('LAMBDA is computed correctly', () => {
    expect(LAMBDA.episodic).toBeCloseTo(Math.LN2 / 7, 5);
  });

  it('DEFAULT_DECAY_CONFIG has expected values', () => {
    expect(DEFAULT_DECAY_CONFIG.strongThreshold).toBe(0.7);
    expect(DEFAULT_DECAY_CONFIG.purgeThreshold).toBe(0.05);
    expect(DEFAULT_DECAY_CONFIG.protectCritical).toBe(true);
  });
});
