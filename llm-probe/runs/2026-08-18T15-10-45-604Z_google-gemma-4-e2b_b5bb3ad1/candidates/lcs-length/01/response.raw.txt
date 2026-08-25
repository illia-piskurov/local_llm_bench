export function solve(input) {
    const A = input.a;
    const B = input.b;

    const m = A.length;
    const n = B.length;

    // dp[i][j] will store the length of LCS of A[0..i-1] and B[0..j-1]
    // Initialize an (m+1) x (n+1) array with zeros
    const dp = Array(m + 1).fill(0).map(() => Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (A[i - 1] === B[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    return dp[m][n];
}