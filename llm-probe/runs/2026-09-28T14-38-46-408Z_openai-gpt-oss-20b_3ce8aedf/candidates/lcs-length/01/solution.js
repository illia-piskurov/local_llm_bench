export function solve(input) {
  const a = input.a;
  const b = input.b;
  const n = a.length;
  const m = b.length;
  // create (n+1) x (m+1) array
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = 0; i < n; i++) {
    const ca = a.charCodeAt(i);
    for (let j = 0; j < m; j++) {
      if (ca === b.charCodeAt(j)) {
        dp[i + 1][j + 1] = dp[i][j] + 1;
      } else {
        const v1 = dp[i][j + 1];
        const v2 = dp[i + 1][j];
        dp[i + 1][j + 1] = v1 > v2 ? v1 : v2;
      }
    }
  }
  return dp[n][m];
}