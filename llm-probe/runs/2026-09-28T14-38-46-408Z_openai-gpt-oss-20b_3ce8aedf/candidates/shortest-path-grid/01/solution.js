export function solve(input) {
  const { grid, start, end } = input;
  const rows = grid.length;
  if (rows === 0) return -1;
  const cols = grid[0].length;
  if (cols === 0) return -1;

  const [sx, sy] = start;
  const [ex, ey] = end;

  if (grid[sx][sy] !== 0 || grid[ex][ey] !== 0) return -1;

  const visited = Array.from({ length: rows }, () => Array(cols).fill(false));
  const queue = [];
  visited[sx][sy] = true;
  queue.push({ x: sx, y: sy, d: 0 });

  const dirs = [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1]
  ];

  while (queue.length) {
    const { x, y, d } = queue.shift();
    if (x === ex && y === ey) return d;
    for (const [dx, dy] of dirs) {
      const nx = x + dx;
      const ny = y + dy;
      if (
        nx >= 0 &&
        nx < rows &&
        ny >= 0 &&
        ny < cols &&
        !visited[nx][ny] &&
        grid[nx][ny] === 0
      ) {
        visited[nx][ny] = true;
        queue.push({ x: nx, y: ny, d: d + 1 });
      }
    }
  }

  return -1;
}