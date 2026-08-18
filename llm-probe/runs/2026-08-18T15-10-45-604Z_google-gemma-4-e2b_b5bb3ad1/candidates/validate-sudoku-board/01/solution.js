export function solve(input) {
    const board = input.board;
    const N = 9;

    // Helper function to check if a specific set of 9 cells is valid (no duplicates among non-'.')
    function checkSet(arr) {
        const seen = new Set();
        for (const char of arr) {
            if (char !== '.') {
                // Ensure the character is a valid digit
                if (char < '1' || char > '9') {
                    return false; 
                }
                // Check for duplicates
                if (seen.has(char)) {
                    return false;
                }
                seen.add(char);
            }
        }
        return true;
    }

    // 1. Check Rows
    for (let i = 0; i < N; i++) {
        if (!checkSet(board[i])) {
            return false;
        }
    }

    // 2. Check Columns
    for (let j = 0; j < N; j++) {
        const column = [];
        for (let i = 0; i < N; i++) {
            column.push(board[i][j]);
        }
        if (!checkSet(column)) {
            return false;
        }
    }

    // 3. Check 3x3 Boxes
    for (let boxRowStart = 0; boxRowStart < N; boxRowStart += 3) {
        for (let boxColStart = 0; boxColStart < N; boxColStart += 3) {
            const box = [];
            
            // Extract the current 3x3 box
            for (let i = boxRowStart; i < boxRowStart + 3; i++) {
                for (let j = boxColStart; j < boxColStart + 3; j++) {
                    box.push(board[i][j]);
                }
            }

            if (!checkSet(box)) {
                return false;
            }
        }
    }

    // If all checks pass
    return true;
}