export function solve(input) {
  const matrix = JSON.parse(JSON.stringify(input.matrix));
  for (let i = 0; i < Math.floor(matrix.length / 2); i++) {
    for (let j = i; j < matrix.length - i - 1; j++) {
      const temp = matrix[i][j];
      matrix[i][j] = matrix[j][matrix.length - 1 - i];
      matrix[j][matrix.length - 1 - i] = matrix[matrix.length - 1 - i][matrix.length - 1 - j];
      matrix[matrix.length - 1 - i][matrix.length - 1 - j] = matrix[matrix.length - 1 - j][i];
      matrix[matrix.length - 1 - j][i] = temp;
    }
  }
  return JSON.parse(JSON.stringify(matrix));
}