export function solve(input) {
    const a = input.a;
    const b = input.b;
    const m = a.length;
    const n = b.length;
    // create 2D array of size (m+1)x(n+1)
    const dp = Array.from({ length: m + 1 }, () => new Uint16Array(n + 1));
    for (let i = 1; i <= m; i++) {
        const ai = a.charCodeAt(i - 1);
        for (let j = 1; j <= n; j++) {
            if (ai === b.charCodeAt(j - 1)) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                const up = dp[i - 1][j];
                const left = dp[i][j - 1];
                dp[i][j] = up > left ? up : left;
            }
        }
    }
    return dp[m][n];
}