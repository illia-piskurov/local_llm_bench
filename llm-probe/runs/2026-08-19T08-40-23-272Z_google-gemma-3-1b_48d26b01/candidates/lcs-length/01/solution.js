export function solve(input) {
  if (!input || !input[0]) {
    return 0;
  }
  let n = input.length;
  let m = input[0].length;

  const dp = Array(n + 1).fill(null).map(() => Array(m + 1).fill(null));

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (input[i - 1] === input[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  return dp[n][m];
}