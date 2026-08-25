export function solve(input) {
    const text = input.text;
    let maxLength = 0;
    let start = 0;

    for (let end = 0; end < text.length; end++) {
        const char = text[end];
        const lastIndex = text.lastIndexOf(char, start);

        if (lastIndex !== -1 && lastIndex >= start) {
            start = lastIndex + 1;
        }

        maxLength = Math.max(maxLength, end - start + 1);
    }

    return maxLength;
}