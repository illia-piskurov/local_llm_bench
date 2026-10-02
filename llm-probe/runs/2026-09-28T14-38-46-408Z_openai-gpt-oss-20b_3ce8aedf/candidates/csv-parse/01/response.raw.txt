export function solve(input) {
  // If input is empty or only whitespace, return []
  if (!input || /^\s*$/.test(input)) return [];

  const rows = [];
  let row = '';
  let field = '';
  let inQuotes = false;
  let i = 0;

  while (i < input.length) {
    const ch = input[i];

    if (inQuotes) {
      if (ch === '"') {
        // Check for escaped quote
        if (i + 1 < input.length && input[i + 1] === '"') {
          field += '"';
          i += 2;
          continue;
        } else {
          inQuotes = false;
          i++;
          continue;
        }
      } else {
        field += ch;
        i++;
        continue;
      }
    } else {
      if (ch === '"') {
        inQuotes = true;
        i++;
        continue;
      } else if (ch === ',') {
        row += field + '\0'; // use null char as separator
        field = '';
        i++;
        continue;
      } else if (ch === '\n' || ch === '\r') {
        // Handle CRLF
        if (ch === '\r' && i + 1 < input.length && input[i + 1] === '\n') {
          i++; // skip LF
        }
        row += field + '\0';
        rows.push(row);
        row = '';
        field = '';
        i++;
        continue;
      } else {
        field += ch;
        i++;
        continue;
      }
    }
  }

  // Add last field and row if any data remains
  if (field !== '' || row !== '') {
    row += field + '\0';
    rows.push(row);
  }

  // Remove possible empty trailing line
  if (rows.length > 0 && rows[rows.length - 1].trim() === '') {
    rows.pop();
  }

  if (rows.length <= 1) return [];

  const headerRow = rows[0];
  const headers = [];
  let buf = '';
  for (let j = 0; j < headerRow.length; j++) {
    const c = headerRow[j];
    if (c === '\0') {
      headers.push(buf.trim());
      buf = '';
    } else {
      buf += c;
    }
  }

  const result = [];

  for (let rIdx = 1; rIdx < rows.length; rIdx++) {
    const rowStr = rows[rIdx];
    const obj = {};
    let idx = 0;
    for (let h = 0; h < headers.length; h++) {
      let valBuf = '';
      while (idx < rowStr.length && rowStr[idx] !== '\0') {
        valBuf += rowStr[idx];
        idx++;
      }
      // skip separator
      if (idx < rowStr.length && rowStr[idx] === '\0') idx++;

      // If value was quoted originally, it already had quotes removed during parsing
      obj[headers[h]] = valBuf;
    }
    result.push(obj);
  }

  return result;
}