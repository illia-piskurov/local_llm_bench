export function solve(input) {
    const { grid, start, end } = input;
    const rows = grid.length;
    const cols = grid[0].length;

    // Check if start and end are valid
    if (
        !grid ||
        !start ||
        !end ||
        rows <= 0 ||
        cols <= 0 ||
        start[0] < 0 || start[0] >= rows ||
        start[1] < 0 || start[1] >= cols ||
        end[0] < 0 || end[0] >= rows ||
        end[1] < 0 || end[1] >= cols
    ) {
        return -1;
    }

    const directions = [[0, 1], [1, 0], [0, -1], [-1, 0]];
    const visited = Array.from({ length: rows }, () => Array(cols).fill(false));

    // BFS function to find minimum number of moves
    function bfs(startPos, endPos) {
        const queue = [[startPos, 0]]; // [position, moves]
        const visitedSet = new Set();

        while (queue.length > 0) {
            const [pos, moves] = queue.shift();
            const [x, y] = pos;

            if (x === endPos[0] && y === endPos[1]) return moves;

            if (visitedSet.has(pos)) continue;
            visitedSet.add(pos);

            for (const [dx, dy] of directions) {
                const nx = x + dx;
                const ny = y + dy;
                if (
                    nx >= 0 &&
                    ny >= 0 &&
                    nx < rows &&
                    ny < cols &&
                    grid[nx][ny] === 0 && // 0-cell is accessible
                    !visitedSet.has([nx, ny])
                ) {
                    queue.push([ [nx, ny], moves + 1 ]);
                }
            }
        }

        return -1;
    }

    const result = bfs(start, end);
    return JSON.stringify(result);
}