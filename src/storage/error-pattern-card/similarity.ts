// Trigger similarity for ADR-006 V3a duplicate detection (v7.6.0).
// Algorithm locked by review and pinned in tests — do not change semantics.
//
// similarity(a, b) = |bigrams(a) ∩ bigrams(b)| / min(|bigrams(a)|, |bigrams(b)|)
//   normalized: lowercase, strip anything outside [a-z0-9 CJK]
//   bigram set over the normalized string (window of 2 code points);
//   a 1-char normalized string degrades to its single char set; empty -> {}
//   empty union -> 0
// Overlap coefficient over bigrams: no word segmentation, so it behaves
// uniformly for English and CJK. Threshold lives in constants.ts
// (SIMILARITY_THRESHOLD, uncalibrated).
export function triggerSimilarity(a: string, b: string): number {
  const bigrams = (s: string): Set<string> => {
    const norm = s.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]/g, "");
    const out = new Set<string>();
    if (norm.length === 1) out.add(norm);
    for (let i = 0; i + 1 < norm.length; i++) out.add(norm.slice(i, i + 2));
    return out;
  };

  const A = bigrams(a);
  const B = bigrams(b);
  const min = Math.min(A.size, B.size);
  if (min === 0) return 0;
  let inter = 0;
  for (const g of A) if (B.has(g)) inter += 1;
  return inter / min;
}
