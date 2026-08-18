export function solve(input) {
    if (!input || typeof input.text !== 'string') {
        return 0;
    }

    const text = input.text;
    let maxLength = 0;
    let start = 0;
    // charIndexMap stores the last seen index of each character
    const charIndexMap = new Map();

    for (let end = 0; end < text.length; end++) {
        const char = text[end];

        if (charIndexMap.has(char)) {
            const lastSeenIndex = charIndexMap.get(char);
            // If the character is a duplicate AND its previous index was within or before our current window start, 
            // we must move the start of the window past that previous occurrence.
            // We use Math.max to ensure 'start' never moves backward if a character appeared outside the current valid window.
            start = Math.max(start, lastSeenIndex + 1);
        }

        // Update the map with the current index for this character
        charIndexMap.set(char, end);

        // Calculate the length of the current unique substring (window size)
        const currentLength = end - start + 1;

        // Update maximum length found so far
        maxLength = Math.max(maxLength, currentLength);
    }

    return maxLength;
}