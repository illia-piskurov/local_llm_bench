export function solve(input) {
  const grid = input.grid;
  const start = input.start;
  const end = input.end;

  const rows = grid.length;
  const cols = grid[0].length;

  const queue = [start];
  const visited = new Set([start.toString()]);

  let moves = 0;

  while (queue.length > 0) {
    const levelSize = queue.length;

    for (let i = 0; i < levelSize; i++) {
      const [x, y] = queue.shift();

      if ([x, y].toString() === end.toString()) {
        return moves;
      }

      const directions = [
        [-1, 0],
        [1, 0],
        [0, -1],
        [0, 1],
      ];

      for (const [dx, dy] of directions) {
        const newX = x + dx;
        const newY = y + dy;

        if (
          newX >= 0 &&
          newX < rows &&
          newY >= 0 &&
          newY < cols &&
          grid[newX][newY] === 0 &&
          !visited.has([newX, newY].toString())
        ) {
          queue.push([newX, newY]);
          visited.add([newX, newY].toString());
        }
      }
    }

    moves++;
  }

  return -1;
}