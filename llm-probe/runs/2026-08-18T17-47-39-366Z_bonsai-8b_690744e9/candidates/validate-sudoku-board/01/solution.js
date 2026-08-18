export function solve(input) {
  const board = input.board;
  
  // Check rows
  for (let i = 0; i < 9; i++) {
    let row = '';
    for (let j = 0; j < 9; j++) {
      row += board[i][j];
    }
    if (!row || containsDuplicate(row)) return false;
  }

  // Check columns
  for (let j = 0; j < 9; j++) {
    let col = '';
    for (let i = 0; i < 9; i++) {
      col += board[i][j];
    }
    if (!col || containsDuplicate(col)) return false;
  }

  // Check 3x3 boxes
  for (let boxRow = 0; boxRow < 3; boxRow++) {
    for (let boxCol = 0; boxCol < 3; boxCol++) {
      let box = '';
      for (let i = boxRow; i < boxRow + 3; i++) {
        for (let j = boxCol; j < boxCol + 3; j++) {
          const index = i * 9 + j;
          box += board[index][index];
        }
      }
      if (!box || containsDuplicate(box)) return false;
    }
  }

  return true;
}

function containsDuplicate(str) {
  let seen = new Set();
  for (let char of str) {
    if (seen.has(char)) return true;
    seen.add(char);
  }
  return false;
}