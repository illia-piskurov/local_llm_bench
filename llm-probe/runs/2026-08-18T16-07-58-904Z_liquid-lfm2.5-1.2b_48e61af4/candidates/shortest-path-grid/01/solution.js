export function solve(input) {
  const { grid, start, end } = input;
  const rows = grid.length;
  const cols = grid[0].length;
  const startX = start[0];
  const startY = start[1];
  const endX = end[0];
  const endY = end[1];

  const directions = [[0,1], [1,0], [0,-1], [-1,0]];
  const visited = Array.from({ length: rows }, () => Array(cols).fill(false));
  let count = 0;

  function isValid(r, c) {
    return r >= 0 && r < rows && c >= 0 && c < cols && grid[r][c] === 0;
  }

  function bfs() {
    const queue = [start];
    visited[start[0]][start[1]] = true;
    while (queue.length > 0) {
      const [x, y] = queue.shift();
      if (x === endX && y === endY) return count;
      for (const [dx, dy] of directions) {
        const nx = x + dx;
        const ny = y + dy;
        if (isValid(nx, ny) && !visited[nx][ny]) {
          visited[nx][ny] = true;
          queue.push([nx, ny]);
        }
      }
    }
    return -1;
  }

  return bfs();
}