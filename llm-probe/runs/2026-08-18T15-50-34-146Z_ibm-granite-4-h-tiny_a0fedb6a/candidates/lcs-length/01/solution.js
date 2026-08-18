export function solve(input) {
    const a = input.a;
    const b = input.b;
    const lenA = a.length;
    const lenB = b.length;
    const dp = Array(lenA + 1).fill(null).map(() => Array(lenB + 1).fill(0));
    
    for (let i = 1; i <= lenA; i++) {
        for (let j = 1; j <= lenB; j++) {
            if (a[i - 1] === b[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    return dp[lenA][lenB];
}