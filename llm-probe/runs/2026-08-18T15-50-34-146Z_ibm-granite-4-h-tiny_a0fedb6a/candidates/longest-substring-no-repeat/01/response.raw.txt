export function solve(input) {
    const text = input.text;
    let maxLength = 0;
    let start = 0;
    const charMap = new Map();

    for (let end = 0; end < text.length; end++) {
        const currentChar = text[end];
        if (charMap.has(currentChar)) {
            start = Math.max(start, charMap.get(currentChar) + 1);
        }
        maxLength = Math.max(maxLength, end - start + 1);
        charMap.set(currentChar, end);
    }

    return maxLength;
}