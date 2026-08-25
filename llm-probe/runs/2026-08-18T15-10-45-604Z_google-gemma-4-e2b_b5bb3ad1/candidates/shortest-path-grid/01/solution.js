export function solve(input) {
    const grid = input.grid;
    const start = input.start;
    const end = input.end;

    if (!grid || grid.length === 0) {
        return -1;
    }

    const R = grid.length;
    const C = grid[0].length;

    const startR = start[0];
    const startC = start[1];
    const endR = end[0];
    const endC = end[1];

    // Check if start or end are blocked (though typically they are assumed valid starting points)
    if (grid[startR][startC] === 1 || grid[endR][endC] === 1) {
        // If the start position itself is blocked, it's unreachable unless start == end and start is allowed.
        // Assuming standard graph traversal rules where start/end must be traversable (0).
        if (startR === endR && startC === endC) {
            return 0;
        }
        return -1;
    }

    // BFS Initialization
    // Queue stores [r, c, distance]
    const queue = [[startR, startC, 0]];
    const visited = new Set();
    visited.add(`${startR},${startC}`);

    // Directions: Up, Down, Left, Right
    const directions = [
        [-1, 0],
        [1, 0],
        [0, -1],
        [0, 1]
    ];

    while (queue.length > 0) {
        const [r, c, dist] = queue.shift();

        if (r === endR && c === endC) {
            return dist;
        }

        for (const [dr, dc] of directions) {
            const nr = r + dr;
            const nc = c + dc;

            // Boundary check
            if (nr >= 0 && nr < R && nc >= 0 && nc < C) {
                // Check if traversable (grid value must be 0) and not visited
                if (grid[nr][nc] === 0 && !visited.has(`${nr},${nc}`)) {
                    visited.add(`${nr},${nc}`);
                    queue.push([nr, nc, dist + 1]);
                }
            }
        }
    }

    // End of BFS: target is unreachable
    return -1;
}