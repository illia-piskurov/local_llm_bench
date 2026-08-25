export function solve(input) {
    const { grid, start, end } = input;
    const rows = grid.length;
    const cols = grid[0].length;
    const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    const visited = Array(rows).fill().map(() => Array(cols).fill(false));
    const queue = [{ x: start[0], y: start[1], steps: 0 }];
    const target = { x: end[0], y: end[1] };

    while (queue.length) {
        const { x, y, steps } = queue.shift();
        if ([x, y] === target && grid[x][y] === 0) return steps;

        visited[x][y] = true;
        for (const [dx, dy] of directions) {
            const nx = x + dx;
            const ny = y + dy;
            if (nx >= 0 && nx < rows && ny >= 0 && ny < cols &&
                !visited[nx][ny] && grid[nx][ny] === 0) {
                queue.push({ x: nx, y: ny, steps: steps + 1 });
            }
        }
    }

    return -1;
}