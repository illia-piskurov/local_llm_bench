export function solve(input) {
    const board = input.board;

    /**
     * Helper function to check if a collection (array of 9 characters) has duplicate non-'.' digits.
     * @param {string[]} line - An array containing the 9 characters to check.
     * @returns {boolean} True if no duplicates, false otherwise.
     */
    function isValidLine(line) {
        const seen = new Set();
        for (const char of line) {
            if (char === '.') continue;
            if (seen.has(char)) {
                return false;
            }
            seen.add(char);
        }
        return true;
    }

    // 1. Check Rows
    for (let r = 0; r < 9; r++) {
        // The row itself is a string, convert it to an array of characters for consistent checking
        if (!isValidLine(Array.from(board[r]))) {
            return false;
        }
    }

    // 2. Check Columns
    for (let c = 0; c < 9; c++) {
        const columnChars = [];
        for (let r = 0; r < 9; r++) {
            columnChars.push(board[r][c]);
        }
        if (!isValidLine(columnChars)) {
            return false;
        }
    }

    // 3. Check 3x3 Boxes
    for (let boxR = 0; boxR < 3; boxR++) { // Box row index (0, 1, 2)
        for (let boxC = 0; boxC < 3; boxC++) { // Box column index (0, 1, 2)
            const boxChars = [];

            // Iterate through the 9 cells within this specific 3x3 box
            for (let rOffset = 0; rOffset < 3; rOffset++) {
                for (let cOffset = 0; cOffset < 3; cOffset++) {
                    // Calculate actual board coordinates
                    const R = boxR * 3 + rOffset;
                    const C = boxC * 3 + cOffset;
                    boxChars.push(board[R][C]);
                }
            }

            if (!isValidLine(boxChars)) {
                return false;
            }
        }
    }

    // If all checks pass
    return true;
}