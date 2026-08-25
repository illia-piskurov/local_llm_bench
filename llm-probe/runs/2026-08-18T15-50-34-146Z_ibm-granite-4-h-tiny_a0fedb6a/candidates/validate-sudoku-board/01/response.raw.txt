export function solve(input) {
  const board = input.board;
  
  for (let i = 0; i < 9; i++) {
    const rowSet = new Set();
    const colSet = new Set();
    const boxSet = new Set();
    
    for (let j = 0; j < 9; j++) {
      const rowChar = board[i][j];
      if (rowChar !== '.') {
        if (rowSet.has(rowChar)) return false;
        rowSet.add(rowChar);
      }
      
      const colChar = board[j][i];
      if (colChar !== '.') {
        if (colSet.has(colChar)) return false;
        colSet.add(colChar);
      }
      
      const boxRow = Math.floor(i / 3) * 3 + Math.floor(j / 3);
      const boxCol = j % 3 * 3;
      const boxChar = board[boxRow][boxCol];
      if (boxChar !== '.') {
        if (boxSet.has(boxChar)) return false;
        boxSet.add(boxChar);
      }
    }
  }
  
  return true;
}