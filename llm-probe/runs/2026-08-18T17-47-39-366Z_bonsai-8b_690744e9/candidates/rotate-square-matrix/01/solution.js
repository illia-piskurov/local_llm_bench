export function solve(input) {
  const matrix = input.matrix;
  const rotated = [];

  for (let i = 0; i < matrix.length; i++) {
    let row = [];
    for (let j = 0; j < matrix[i].length; j++) {
      row.push(matrix[row.length - 1 - j][i]);
    }
    rotated.push(row);
  }

  return rotated;
}