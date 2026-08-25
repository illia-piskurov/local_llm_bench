export function solve(input) {
    return JSON.parse(JSON.stringify(input.matrix.map(row => row.reverse()).reverse()));
}