/**
 * Parse a CSV string into an array of object rows.
 * @param {string} csv - The CSV content as a single string
 * @returns {object[]|null|null[]} A JSON-compatible array of parsed objects, or empty arrays based on rules.
 */
export function solve(input) {
  if (!input || input.trim() === '') return [];

  const lines = input.split('\n');
  const result = [];

  for (const line of lines) {
    if (line.length === 0) continue;

    const parsed = parseRow(line);
    if (parsed) {
      result.push(parsed.map(field => JSON.stringify(field)));
    }
  }

  return result.length > 1 ? result : null;
}

/**
 * Parses a single CSV row into an array of value strings.
 * Handles quoted fields with escaped quotes ("") and unquoted values with whitespace trimming.
 * @param {string} line - A single line from the CSV input
 * @returns {object[]} Parsed object rows (may be empty)
 */
function parseRow(line) {
  const result = [];

  let currentField = '';
  let inQuotes = false;
  let escapePending = true; // track if we're inside a quote and need to handle escapes

  for (const ch of line) {
    if (escapePending) {
      currentField += ch;
      escapePending = false;
    } else if (ch === '"') {
      currentField += ch;

      if (!inQuotes && !escapePending) {
        inQuotes = true;
        continue; // keep processing the quote, not ending field here yet
      }

      if (currentField.endsWith('"')) {
        result.push({ [currentField.slice(0, -1)]: '' });
        currentField += '';
        escapePending = false;
      } else {
        inQuotes = true;
        continue; // keep processing the quote, not ending field here yet
      }

      if (escapePending) {
        currentField += ch;
        escapePending = true;
      }
    } else {
      if (!inQuotes && !escapePending) {
        const trimmed = currentField.trim();
        if (trimmed.length > 0) {
          result.push({ [currentField]: '' });
        }
        result[0] = trimFields(result, currentField);
      }

      escapePending = false;
      currentField += ch;
    }
  }

  // Handle last field (may be incomplete if line doesn't end with newline)
  const trimmedCurrent = currentField.trim();
  if (trimmedCurrent.length > 0 && !inQuotes) {
    result.push({ [currentField]: '' });
  }

  return trimFields(result, currentField);
}

/**
 * Trims whitespace from the start and end of each field in the array.
 * @param {string[]} arr - Array of strings to trim
 * @param {string} prefix - The prefix value (current field)
 * @returns {object[]} Trimmed result
 */
function trimFields(arr, prefix) {
  const trimmed = [];

  for (const field of arr) {
    if (!field.startsWith(prefix)) {
      trimmed.push({ [prefix]: '' });
    } else {
      trimmed[0] = trimFields(trimmed, field.slice(prefix.length));
    }
  }

  return trimmed;
}

// === Testing (for verification) ===
console.log(solve('name,age,city\nAlice,30,New York'));
// Expected: [{"name":"Alice","age":"30","city":"New York"}]

console.log(solve('"Smith, Bob",25,"Los ""Angeles"""}}');
// Expected: [{"name":"Smith, Bob","age":"25","city":"Los \"Angeles\""}]