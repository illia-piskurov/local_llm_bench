export function solve(input) {
    if (!input || input.trim() === '') {
        return [];
    }

    const rows = input.split('\n');
    const headerRow = rows[0].trim();
    
    if (!headerRow) {
        return [];
    }

    // Parse header row to get column names
    const headers = [];
    let current = '';
    let inQuote = false;
    let i = 0;
    
    while (i < headerRow.length) {
        if (headerRow[i] === '"') {
            inQuote = !inQuote;
            i++;
            continue;
        }
        
        if (!inQuote && headerRow[i] === ',') {
            headers.push(current.trim());
            current = '';
        } else {
            current += headerRow[i];
        }
        i++;
    }
    
    if (current.trim() !== '') {
        headers.push(current.trim());
    }
    
    const result = [];
    
    // Process data rows
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i].trim();
        if (!row) continue;
        
        const rowData = {};
        let current = '';
        let inQuote = false;
        let j = 0;
        
        while (j < row.length) {
            if (row[j] === '"') {
                inQuote = !inQuote;
                j++;
                continue;
            }
            
            if (!inQuote && row[j] === ',') {
                rowData[current.trim()] = current.trim();
                current = '';
            } else {
                current += row[j];
            }
            j++;
        }
        
        if (current.trim() !== '') {
            rowData[current.trim()] = current.trim();
        }
        
        // Map values to headers
        const rowHeaders = [];
        let tempCurrent = '';
        let tempInQuote = false;
        let tempJ = 0;
        
        while (tempJ < row.length) {
            if (row[tempJ] === '"') {
                tempInQuote = !tempInQuote;
                tempJ++;
                continue;
            }
            
            if (!tempInQuote && row[tempJ] === ',') {
                rowHeaders.push(tempCurrent.trim());
                tempCurrent = '';
            } else {
                tempCurrent += row[tempJ];
            }
            tempJ++;
        }
        
        if (tempCurrent.trim() !== '') {
            rowHeaders.push(tempCurrent.trim());
        }
        
        // Map the values to headers
        for (let k = 0; k < headers.length; k++) {
            const key = headers[k];
            const value = rowHeaders[k];
            rowData[key] = value;
        }
        
        result.push(rowData);
    }
    
    return result;
}