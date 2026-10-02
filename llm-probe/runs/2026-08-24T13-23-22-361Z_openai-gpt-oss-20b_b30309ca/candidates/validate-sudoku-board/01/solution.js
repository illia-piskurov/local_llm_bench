export function solve(input) {
  const board = input.board;
  // Helper to check if a set of 9 cells contains no duplicates except '.'
  const isValidGroup = (cells) => {
    const seen = new Set();
    for (const c of cells) {
      if (c === '.') continue;
      if (seen.has(c)) return false;
      seen.add(c);
    }
    return true;
  };

  // Check rows
  for (let r = 0; r < 9; r++) {
    const row = board[r].split('');
    if (!isValidGroup(row)) return false;
  }

  // Check columns
  for (let c = 0; c < 9; c++) {
    const col = [];
    for (let r = 0; r < 9; r++) col.push(board[r][c]);
    if (!isValidGroup(col)) return false;
  }

  // Check 3x3 boxes
  for (let br = 0; br < 3; br++) {
    for (let bc = 0; bc < 3; bc++) {
      const box = [];
      for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 3; c++) {
          box.push(board[br * 3 + r][bc * 3 + c]);
        }
      }
      if (!isValidGroup(box)) return false;
    }
  }

  return true;
}