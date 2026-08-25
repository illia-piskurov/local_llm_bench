export function solve(input) {
    const { grid, start, end } = input;
    const rows = grid.length;
    const cols = grid[0].length;

    const queue = [[start]];
    let steps = 0;

    while (queue.length > 0) {
        const levelSize = queue.length;
        for (let i = 0; i < levelSize; i++) {
            const [x, y] = queue.shift();
            if ([x, y].join() === end.join()) return steps;

            const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];

            for (const [dx, dy] of directions) {
                const newX = x + dx;
                const newY = y + dy;

                if (newX < 0 || newX >= rows || newY < 0 || newY >= cols || grid[newX][newY] === 1) continue;

                queue.push([newX, newY]);
            }
        }

        steps++;
    }

    return -1;
}