export function solve(input) {
  const board = input.board;
  const rows = Array.from({ length: 9 }, () => new Set());
  const cols = Array.from({ length: 9 }, () => new Set());
  const boxes = Array.from({ length: 9 }, () => new Set());

  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const char = board[r][c];
      if (char === '.') continue;

      const boxIdx = Math.floor(r / 3) * 3 + Math.floor(c / 3);

      if (rows[r].has(char) || cols[c].has(char) || boxes[boxIdx].has(char)) {
        return false;
      }

      rows[r].add(char);
      cols[c].add(char);
      boxes[boxIdx].add(char);
    }
  }

  return true;
}