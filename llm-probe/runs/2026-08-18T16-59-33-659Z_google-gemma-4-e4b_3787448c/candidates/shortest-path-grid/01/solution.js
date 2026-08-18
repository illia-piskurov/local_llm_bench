export function solve(input) {
    const grid = input.grid;
    if (!grid || grid.length === 0) return -1;

    const R = grid.length;
    const C = grid[0].length;

    let startR = input.start[0];
    let startC = input.start[1];
    let endR = input.end[0];
    let endC = input.end[1];

    // Directions: Up, Down, Left, Right
    const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];

    // Queue for BFS: stores [r, c, distance]
    // We use an array as a queue (push/shift)
    let queue = [];
    queue.push([startR, startC, 0]);

    // Visited tracking set using string keys "r,c"
    // Since we are looking for the minimum path length, marking visited is sufficient.
    let visited = new Set();
    visited.add(`${startR},${startC}`);

    while (queue.length > 0) {
        const [r, c, dist] = queue.shift();

        // Check if we reached the target
        if (r === endR && c === endC) {
            return dist;
        }

        // Explore neighbors
        for (const [dr, dc] of directions) {
            const nr = r + dr;
            const nc = c + dc;
            const key = `${nr},${nc}`;

            // 1. Boundary check
            if (nr < 0 || nr >= R || nc < 0 || nc >= C) {
                continue;
            }

            // 2. Blocked cell check (Must be 0)
            if (grid[nr][nc] === 1) {
                continue;
            }

            // 3. Visited check
            if (visited.has(key)) {
                continue;
            }

            // If valid, enqueue and mark visited
            visited.add(key);
            queue.push([nr, nc, dist + 1]);
        }
    }

    // If the queue empties before reaching the end point
    return -1;
}