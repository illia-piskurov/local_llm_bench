export function solve(input) {
    const csv = input.csv;
    
    // Split the CSV string into rows using newline as a delimiter
    const rows = csv.split(/\r?\n/);

    // Remove any trailing empty lines
    while (rows.length > 0 && rows[rows.length - 1] === '') {
        rows.pop();
    }

    // If there are no rows or only the header row, return an empty array
    if (rows.length <= 1) {
        return [];
    }

    const headers = rows.shift().split(',');

    // Parse each row into an object using the headers as keys
    return rows.map(row => {
        const values = row.split(',');
        const result = {};
        for (let i = 0; i < headers.length; i++) {
            const value = values[i];
            if (value.startsWith('"') && value.endsWith('"')) {
                // Unescape escaped quotes
                result[headers[i]] = value.slice(1, -1).replace(/""/g, '"');
            } else {
                // Trim whitespace and preserve internal whitespace in quoted values
                result[headers[i]] = value.trim();
            }
        }
        return result;
    });
}