export function solve(input) {
    const text = input.text;
    let maxLength = 0;
    let left = 0;
    const charSet = new Set();

    for (let right = 0; right < text.length; right++) {
        // If the character at 'right' is already in the current window [left, right-1]
        while (charSet.has(text[right])) {
            // Shrink the window from the left until the duplicate is removed
            charSet.delete(text[left]);
            left++;
        }

        // Expand the window to include text[right]
        charSet.add(text[right]);

        // Update the maximum length found so far
        // The current length is (right - left + 1)
        maxLength = Math.max(maxLength, right - left + 1);
    }

    return maxLength;
}