export function solve(input) {
    const matrix = input.matrix;
    if (!matrix || matrix.length === 0) {
        return [];
    }

    const rows = matrix.length;
    const cols = matrix[0].length;

    // The new matrix will have dimensions (cols x rows)
    // Initialize the result matrix structure: 'rows' number of arrays, each of size 'cols'.
    let rotatedMatrix = [];
    for (let i = 0; i < cols; i++) {
        rotatedMatrix[i] = Array(rows).fill(undefined);
    }

    // Transformation rule for 90 degrees clockwise:
    // Original coordinates (r, c) move to new coordinates (c, rows - 1 - r)
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const newValue = matrix[r][c];
            // In the rotated matrix:
            // New row index = original column index (c)
            const newRow = c;
            // New column index = rows - 1 - original row index (r)
            const newCol = rows - 1 - r;

            rotatedMatrix[newRow][newCol] = newValue;
        }
    }

    return rotatedMatrix;
}