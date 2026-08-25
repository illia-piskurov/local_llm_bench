export function solve(input) {
    const csvString = input && typeof input === 'object' && typeof input.csv !== 'undefined' ? input.csv : "";

    if (!csvString.trim()) {
        return [];
    }

    // 1. Split the entire string into potential rows, handling various line endings.
    // We split by \r?\n to handle both LF (\n) and CRLF (\r\n).
    let lines = csvString.split(/\r?\n/);

    // Filter out empty strings resulting from trailing newlines or blank input sections.
    const trimmedLines = lines.map(line => line.trimEnd()).filter((line, index, arr) => {
        // Keep the first potentially non-empty line (header), but ignore fully empty lines otherwise.
        if (index === 0 && line !== "") return true;
        return line !== "";
    });

    if (trimmedLines.length === 0) {
        return [];
    }

    /**
     * Parses a single CSV line into an array of fields, respecting quotes and escaped quotes.
     * Uses regex iterative execution for reliable tokenization.
     * @param {string} line - The raw CSV line string.
     * @returns {string[]} Array of parsed field values.
     */
    const getFields = (line) => {
        const fields = [];
        // Regex Explanation:
        // 1. "([^"]*(?:""[^"]*)*)" : Captures a quoted string. The content is in group 1.
        //    - [^"]* : Any non-quote characters.
        //    - (?:""[^"]*)* : Non-capturing group for repeated escaped quotes ("") followed by more non-quotes.
        // 2. |([^,]*): OR captures an unquoted string (anything up to a comma). The content is in group 2.
        const csvRegex = /(?:"([^"]*(?:""[^"]*)*)"|([^,]*))/g;
        
        let match;
        let lastIndex = 0;

        // Iterate over all matches found by the regex in the line
        while ((match = csvRegex.exec(line)) !== null) {
            // match[1] holds content of quoted field (if present)
            // match[2] holds content of unquoted field (if present)
            
            let value;
            if (match[1] !== undefined && match[1].length > 0) {
                // Quoted Value: Unescape "" to "
                value = match[1].replace(/""/g, '"');
            } else if (match[2] !== undefined) {
                // Unquoted Value: Trim whitespace. Handles empty fields between commas correctly.
                value = match[2].trim();
            } else {
                // Should theoretically not happen for valid CSV structure but defaults to empty string
                value = "";
            }

            fields.push(value);
        }
        return fields;
    };


    // 2. Process the Header Row (Row 0)
    const headerLine = trimmedLines[0];
    const headers = getFields(headerLine);

    if (headers.length === 0 || (trimmedLines.length > 1 && !headerLine)) {
         return []; // Handles case where only blank lines exist
    }


    // 3. Process Data Rows (Row 1 onwards)
    const results = [];
    for (let i = 1; i < trimmedLines.length; i++) {
        const dataLine = trimmedLines[i];
        if (!dataLine) continue;

        const values = getFields(dataLine);
        const obj = {};

        // Ensure the number of keys matches the number of values found, 
        // padding or truncating as necessary (assuming structure is maintained).
        for (let j = 0; j < headers.length; j++) {
            obj[headers[j]] = values[j] !== undefined ? values[j] : "";
        }

        results.push(obj);
    }

    return results;
}