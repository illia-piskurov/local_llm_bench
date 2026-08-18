export function solve(input) {
    const matrix = input.matrix;
    if (!matrix || matrix.length === 0) {
        return [];
    }

    const R = matrix.length; // Number of rows in input
    const C = matrix[0].length; // Number of columns in input

    // The rotated matrix will have C rows and R columns
    const result = Array(C).fill(0).map(() => Array(R));

    // 90-degree clockwise rotation logic:
    // The j-th column of the input matrix becomes the j-th row of the result, reversed.
    for (let j = 0; j < C; j++) { // j iterates over the old columns (which become new rows)
        let newRow = [];
        for (let i = 0; i < R; i++) { // i iterates over the old rows (forming the elements of the new row)
            // The element at matrix[i][j] moves to result[j][R - 1 - i] if we were transposing and flipping.
            // Based on example: Column j of M forms Row j of R, but reversed.
            newRow.push(matrix[R - 1 - i][j]);
        }
        result[j] = newRow;
    }

    return result;
}