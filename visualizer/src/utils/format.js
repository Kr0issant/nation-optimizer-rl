// Tiny formatters used everywhere.

export function fmt(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(digits)}M`;
  if (Math.abs(n) >= 10_000) return `${(n / 1000).toFixed(digits)}k`;
  if (Math.abs(n) >= 100) return n.toFixed(0);
  if (Math.abs(n) >= 10) return n.toFixed(1);
  if (Math.abs(n) >= 1) return n.toFixed(2);
  if (Math.abs(n) >= 0.01) return n.toFixed(3);
  return n.toExponential(2);
}

export function fmtPct(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return `${(n * 100).toFixed(0)}%`;
}

export function fmtSigned(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(digits)}`;
}
