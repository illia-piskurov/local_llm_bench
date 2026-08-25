export function solve(input) {
  const csv = input?.csv || "";
  if (!csv.trim()) return [];

  const rawRows = csv.split(/[\n\r]+/).filter(r => r);
  if (rawRows.length === 1) return [];

  // Parse a single row into an array of field strings
  const parseRow = str => {
    const fields = [];
    let cur = "";
    let inQuotes = false;
    for (let i = 0; i < str.length; i++) {
      if (inQuotes) {
        // handle escaped quotes: "" -> '
        if (i + 1 < str.length && str[i] === '"' && str[i + 1] === '"') {
          cur += "'";
          i++;
          continue;
        }
        // newline inside a quoted field does NOT end the field
      } else {
        if (str[i] === '\"') inQuotes = true;
        else if (str[i] === '\n' || str[i] === '\r') {
          fields.push(cur);
          cur = "";
        } else {
          cur += str[i];
        }
      }
    }
    fields.push(cur);
    return fields;
  };

  const [headerRow, ...dataRows] = rawRows;
  const headers = parseRow(headerRow);

  const result = [];
  for (const row of dataRows) {
    const obj = {};
    for (let j = 0; j < headers.length; j++) {
      let val = parseRow(row)[j];
      // trim only unquoted values
      if (!val.startsWith('\"') && !val.endsWith('\"')) val = val.trim();
      obj[headers[j]] = val;
    }
    result.push(obj);
  }

  return result;
}