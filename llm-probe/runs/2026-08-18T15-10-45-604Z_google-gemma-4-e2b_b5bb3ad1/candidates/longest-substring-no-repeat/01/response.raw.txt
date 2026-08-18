export function solve(input) {
    const text = input.text;
    if (!text || text.length === 0) {
        return 0;
    }

    let left = 0;
    let maxLength = 0;
    const lastSeen = new Map(); // Stores character -> index of its last appearance

    for (let right = 0; right < text.length; right++) {
        const charRight = text[right];

        if (lastSeen.has(charRight)) {
            const lastIndex = lastSeen.get(charRight);
            // If the last occurrence of this character is within the current window [left, right],
            // we must move the left pointer past that last occurrence to ensure no duplicates remain.
            if (lastIndex >= left) {
                left = lastIndex + 1;
            }
        }

        // Update the last seen index for the current character
        lastSeen.set(charRight, right);

        // Calculate the current window length and update max length
        maxLength = Math.max(maxLength, right - left + 1);
    }

    return maxLength;
}