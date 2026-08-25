export function solve(input) {
    const grid = input.grid;
    if (!grid || grid.length === 0 || grid[0].length === 0) return -1;

    const startR = input.start[0];
    const startC = input.start[1];
    const endR = input.end[0];
    const endC = input.end[1];

    const R = grid.length;
    const C = grid[0].length;

    // Check if start or end are fundamentally out of bounds (Safety check)
    if (startR < 0 || startR >= R || startC < 0 || startC >= C ||
        endR < 0 || endR >= R || endC < 0 || endC >= C) {
        // If coordinates are invalid, they cannot be reached.
        return -1;
    }

    // Check if start/end cells themselves are blocked (The path requires starting on a valid cell)
    if (grid[startR][startC] === 1 || grid[endR][endC] === 1) {
        // If start or end is blocked, no movement can occur through it.
        // We must assume the problem context allows this check, though usually start/end are guaranteed traversable (0).
        if (startR !== endR || startC !== endC) {
            return -1;
        }
    }


    // BFS Initialization: queue stores [r, c, distance]
    let queue = [];
    queue.push([startR, startC, 0]);

    // Visited set uses a string key "r,c"
    let visited = new Set();
    visited.add(`${startR},${startC}`);

    const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];

    while (queue.length > 0) {
        // Dequeue
        const current = queue.shift();
        const r = current[0];
        const c = current[1];
        const d = current[2];

        // Check for Goal
        if (r === endR && c === endC) {
            return d;
        }

        // Explore Neighbors
        for (const [dr, dc] of directions) {
            const nr = r + dr;
            const nc = c + dc;

            // 1. Check bounds
            if (nr < 0 || nr >= R || nc < 0 || nc >= C) {
                continue;
            }

            // 2. Check if blocked (must be 0)
            if (grid[nr][nc] === 1) {
                continue;
            }

            // 3. Check visited status
            const key = `${nr},${nc}`;
            if (!visited.has(key)) {
                // Found a valid, unvisited neighbor
                visited.add(key);
                queue.push([nr, nc, d + 1]);
            }
        }
    }

    // If the queue empties and the end was never reached
    return -1;
}