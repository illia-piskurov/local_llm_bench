export function solve(input) {
    const s = input.text;
    const seen = new Map();
    let maxLen = 0;
    let start = 0;
    for (let i = 0; i < s.length; i++) {
        const ch = s[i];
        if (seen.has(ch)) {
            const prevIndex = seen.get(ch);
            if (prevIndex >= start) {
                start = prevIndex + 1;
            }
        }
        seen.set(ch, i);
        const currentLen = i - start + 1;
        if (currentLen > maxLen) maxLen = currentLen;
    }
    return maxLen;
}