export function solve(input) {
    const csv = input.csv;
    if (!csv || !csv.trim()) return [];

    const lines = csv.split('\n').filter(Boolean);
    if (lines.length < 2) return [];

    const headers = lines[0].split(',');
    const dataRows = lines.slice(1).map(row => {
        const parts = [];
        let currentPart = '';
        let inQuotes = false;

        for (const char of row) {
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                parts.push(currentPart.trim());
                currentPart = '';
            } else {
                currentPart += char;
            }
        }

        parts.push(currentPart.trim());
        return parts;
    });

    const result = headers.map((header, index) => ({
        [header]: dataRows[index]
    }));

    return result;
}