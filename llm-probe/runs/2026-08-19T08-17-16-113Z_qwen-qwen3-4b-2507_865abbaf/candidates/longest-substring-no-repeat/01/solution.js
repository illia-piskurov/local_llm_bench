export function solve(input) {
    if (!input || input.length === 0) {
        return 0;
    }
    
    let maxLength = 0;
    let left = 0;
    let charIndexMap = {};
    
    for (let right = 0; right < input.length; right++) {
        const char = input[right];
        
        if (charIndexMap[char] !== undefined && charIndexMap[char] >= left) {
            left = charIndexMap[char] + 1;
        }
        
        charIndexMap[char] = right;
        
        maxLength = Math.max(maxLength, right - left + 1);
    }
    
    return maxLength;
}