export function solve(input) {
  const matrix = input.matrix;
  if (!matrix || matrix.length === 0) {
    return [];
  }

  const rows = matrix.length;
  const cols = matrix[0].length;

  // The new matrix dimensions will be (cols x rows).
  // The element at original coordinates (r, c) moves to the new coordinates (c, n-1-r), where n is the number of rows (original height).
  // Example: 2x3 matrix. New matrix is 3x2.
  // Original (0, 0) -> New (0, 1) (bottom left corner if we view it as a rotation) -- Wait, let's stick to indices.

  /*
    Original (r, c):
    [[A, B, C],
     [D, E, F]]
    (2 rows, 3 cols)

    Rotated 90 degrees clockwise:
    [[D, A],
     [E, B],
     [F, C]]
    (3 rows, 2 cols)
  */

  // New matrix dimensions: Height = Old Columns (cols), Width = Old Rows (rows).
  const rotatedMatrix = Array.from({ length: cols }, () => new Array(rows));

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      // Original element at matrix[r][c] moves to the new position.
      // The row index of the rotated matrix corresponds to the original column index 'c'.
      const newRow = c;
      // The column index of the rotated matrix corresponds to (rows - 1) - original row index 'r'.
      const newCol = rows - 1 - r;

      rotatedMatrix[newRow][newCol] = matrix[r][c];
    }
  }

  return rotatedMatrix;
}