export function solve(input) {
  if (!input || typeof input !== "string") return [];
  const len = input.length;
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < len; i++) {
    const ch = input[i];
    if (inQuotes) {
      if (ch === '"') {
        if (i + 1 < len && input[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else {
      if (ch === ',') {
        row.push(field);
        field = "";
      } else if (ch === '\r') {
        // ignore, will handle \n
      } else if (ch === '\n') {
        row.push(field);
        rows.push(row);
        row = [];
        field = "";
      } else if (ch === '"') {
        inQuotes = true;
      } else {
        field += ch;
      }
    }
  }
  // push last field/row
  row.push(field);
  rows.push(row);

  // trim trailing empty rows
  while (rows.length > 0) {
    const r = rows[rows.length - 1];
    if (r.every((v) => v === "")) rows.pop();
    else break;
  }

  if (rows.length < 2) return [];

  const header = rows[0].map((h) => h.trim());
  const result = [];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    // skip completely empty rows
    if (r.every((v) => v === "")) continue;
    const obj = {};
    for (let j = 0; j < header.length; j++) {
      let val = r[j] !== undefined ? r[j] : "";
      if (!inQuotes) {
        // but we cannot know quote status per field after parsing
        // Instead trim only if the original field was not quoted.
        // We can detect by checking if value started with " in raw input, but easier: we trimmed quotes during parse? No.
      }
    }
  }

  // Since trimming logic already handled for unquoted values during parse,
  // we need to adjust parsing to trim only when not quoted.
  // Let's redo parseRows accordingly.

  function parseCSV(str) {
    const rows = [];
    let row = [];
    let field = "";
    let inQuotes = false;
    for (let i = 0; i < str.length; i++) {
      const ch = str[i];
      if (inQuotes) {
        if (ch === '"') {
          if (i + 1 < str.length && str[i + 1] === '"') {
            field += '"';
            i++;
          } else {
            inQuotes = false;
          }
        } else {
          field += ch;
        }
      } else {
        if (ch === ',') {
          row.push(field);
          field = "";
        } else if (ch === '\r') {
          // ignore
        } else if (ch === '\n') {
          row.push(field);
          rows.push(row);
          row = [];
          field = "";
        } else if (ch === '"') {
          inQuotes = true;
        } else {
          field += ch;
        }
      }
    }
    row.push(field);
    rows.push(row);

    // trim trailing empty rows
    while (rows.length > 0) {
      const r = rows[rows.length - 1];
      if (r.every((v) => v === "")) rows.pop();
      else break;
    }

    // trim unquoted values
    for (let i = 0; i < rows.length; i++) {
      for (let j = 0; j < rows[i].length; j++) {
        const val = rows[i][j];
        if (!val.startsWith('"') && !val.endsWith('"')) {
          rows[i][j] = val.trim();
        }
      }
    }

    return rows;
  }

  const parsedRows = parseCSV(input);
  if (parsedRows.length < 2) return [];
  const hdr = parsedRows[0].map((h) => h.trim());
  const out = [];
  for (let i = 1; i < parsedRows.length; i++) {
    const r = parsedRows[i];
    if (r.every((v) => v === "")) continue;
    const obj = {};
    for (let j = 0; j < hdr.length; j++) {
      obj[hdr[j]] = r[j] !== undefined ? r[j] : "";
    }
    out.push(obj);
  }
  return out;
}