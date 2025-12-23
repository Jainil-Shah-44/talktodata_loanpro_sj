// 1 Crore = 10,000,000
export const CRORE_DIVISOR = 10_000_000;

export function toCrores(
  value: number | null | undefined,
  decimals = 2
): number | null {
  if (value === null || value === undefined) return null;
  return Number((value / CRORE_DIVISOR).toFixed(decimals));
}

export function formatCrores(
  value: number | null | undefined,
  decimals = 2
): string {
  const cr = toCrores(value, decimals);
  if (cr === null) return "-";
  return `${cr.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })} Cr`;
}