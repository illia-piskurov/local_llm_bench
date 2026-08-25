export function solve(input) {
    // Check if a 9x9 Sudoku board is valid
    const board = input.board;
    
    // Helper function to check if a row, column, or 3x3 box has duplicates
    function isValidGroup(group) {
        const seen = new Set();
        for (let cell of group) {
            if (cell !== '.') {
                if (seen.has(cell)) {
                    return false;
                }
                seen.add(cell);
            }
        }
        return true;
    }
    
    // Check each row
    for (let row = 0; row < 9; row++) {
        const rowGroup = [];
        for (let col = 0; col < 9; col++) {
            rowGroup.push(board[row][col]);
        }
        if (!isValidGroup(rowGroup)) {
            return false;
        }
    }
    
    // Check each column
    for (let col = 0; col < 9; col++) {
        const colGroup = [];
        for (let row = 0; row < 9; row++) {
            colGroup.push(board[row][col]);
        }
        if (!isValidGroup(colGroup)) {
            return false;
        }
    }
    
    // Check each 3x3 box
    for (let boxRow = 0; boxRow < 3; boxRow++) {
        for (let boxCol = 0; boxCol <  3; boxCol++) {
            const boxGroup = [];
            for (let row = 0; row < 3; row++) {
                for (let col = 0; col < 3; col++) {
                    const r = boxRow * 3 + row;
                    const c = boxCol * 3 + col;
                    boxGroup.push(board[r][c]);
                }
            }
            if (!isValidGroup(boxGroup)) {
                return false;
            }
        }
    }
    
    return true;
}