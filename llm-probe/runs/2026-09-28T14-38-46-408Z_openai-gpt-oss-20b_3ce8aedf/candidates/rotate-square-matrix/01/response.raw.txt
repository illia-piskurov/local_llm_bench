export function solve(input) {
  const m = input.matrix;
  const nRows = m.length;
  if (nRows === 0) return [];
  const nCols = m[0].length;
  const result = Array.from({ length: nCols }, () => new Array(nRows));
  for (let i = 0; i < nRows; i++) {
    for (let j = 0; j < nCols; j++) {
      result[j][nRows - i - 1] = m[i][j];
    }
  }
  return result;
}