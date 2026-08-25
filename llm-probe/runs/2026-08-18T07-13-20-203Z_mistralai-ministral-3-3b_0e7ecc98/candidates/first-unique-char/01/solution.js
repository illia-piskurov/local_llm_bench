export function solve(input) {
    const text = input.text;
    const charCount = new Map();
    for (const char of text) {
        charCount.set(char, (charCount.get(char) || 0) + 1);
    }
    for (let i = 0; i < text.length; i++) {
        if (charCount.get(text[i]) === 1) return i;
    }
    return -1;
}