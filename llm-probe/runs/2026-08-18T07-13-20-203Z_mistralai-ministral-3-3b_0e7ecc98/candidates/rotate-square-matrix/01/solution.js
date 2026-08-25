export function solve(input) {
    const matrix = [...input.matrix];
    return matrix.map((row, i) => row.reverse()).reverse();
}