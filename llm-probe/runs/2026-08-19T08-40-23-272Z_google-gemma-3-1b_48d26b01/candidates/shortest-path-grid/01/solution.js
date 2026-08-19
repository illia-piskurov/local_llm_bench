export function solve(input) {
  let start = input.start;
  let end = input.end;

  if (start === end) {
    return 0;
  }

  let queue = [[start, 1]];
  let visited = new Set();
  visited.add(start);

  while (queue.length > 0) {
    let current = queue.shift();
    let row = current[0];
    let col = current[1];

    if (row === end) {
      return queue.length;
    }

    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;

        let newRow = row + dr;
        let newCol = col + dc;

        if (!newRow >= 0 && !newRow < input.grid.length && !newCol >= 0 && !newCol < input.grid[0].length && !visited.has(`${newRow},${newCol}`) && input.grid[newRow][newCol] === 0) {
          queue.push([newRow, newCol]);
          visited.add(`${newRow},${newCol}`);
        }
      }
    }
  }

  return -1;
}