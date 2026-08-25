export function solve(input) {
    const board = input.board;

    // Helper to check if a number is valid in a given row, column, or 3x3 box.
    function isValid(num, posRow, posCol) {
        for (let i = 0; i < 9; i++) {
            // Check current row and column
            if (board[posRow][i] === num || board[i][posCol] === num) return false;
            // Check 3x3 box
            const boxRowStart = Math.floor(posRow / 3) * 3;
            const boxColStart = Math.floor(posCol / 3) * 3;
            if (board[boxRowStart + i % 3][boxColStart + i / 3] === num) return false;
        }
        return true;
    }

    // Check each cell in the board
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            const currentChar = board[row][col];
            if (currentChar !== '.') { // Only check non-empty cells
                if (!isValid(currentChar, row, col)) return false;
            }
        }
    }

    return true;
}