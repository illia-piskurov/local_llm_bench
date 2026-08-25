export function solve(input) {
    const board = input.board;

    // Helper function to check a unit (row, column, or 3x3 box)
    function isValidUnit(unitChars) {
        const seen = new Set();
        for (const char of unitChars) {
            if (char === '.') continue;
            if (seen.has(char)) return false;
            seen.add(char);
        }
        return true;
    }

    // 1. Check Rows
    for (let i = 0; i < 9; i++) {
        const rowChars = board[i].split('');
        if (!isValidUnit(rowChars)) {
            return false;
        }
    }

    // 2. Check Columns
    for (let j = 0; j < 9; j++) {
        const colChars = [];
        for (let i = 0; i < 9; i++) {
            colChars.push(board[i][j]);
        }
        if (!isValidUnit(colChars)) {
            return false;
        }
    }

    // 3. Check 3x3 Boxes
    for (let boxRow = 0; boxRow < 9; boxRow += 3) {
        for (let boxCol = 0; boxCol < 9; boxCol += 3) {
            const boxChars = [];
            for (let i = 0; i < 3; i++) {
                for (let j = 0; j < 3; j++) {
                    boxChars.push(board[boxRow + i][boxCol + j]);
                }
            }
            if (!isValidUnit(boxChars)) {
                return false;
            }
        }
    }

    // If all checks pass
    return true;
}