/**
 * Parse a URL query string into a plain object.
 * Input is expected to be of the form {"query":"..."}
 */
export function solve(input) {
  // Strip leading '{' and trailing '}' to get just the query value
  const query = (input || {}).query?.replace(/^"/, '').replace(/"$/, '');

  if (!query) return {};

  let result = parseQueryString(query);
  return Object.fromEntries(
    new Map([...result.entries()].sort(([a], [b]) => a.localeCompare(b))
  );
}

/**
 * Parse individual query string segments into key-value pairs.
 */
function parseQueryString(query) {
  const parts = query.split('&');
  let currentKey = null;
  let currentValue = '';

  for (const segment of parts) {
    if (!segment || segment.startsWith('#')) continue;

    const eqIndex = segment.indexOf('=');

    let key, value;

    if (eqIndex !== -1) {
      key = decodeURIComponent(segment.slice(0, eqIndex));
      value = decodeURIComponent(segment.slice(eqIndex + 1));
    } else {
      // No '=' means the value is boolean true
      currentKey = segment;
      currentValue = 'true';

      if (currentKey.endsWith('[]')) {
        key = segment.replace(/(\[\])$/, '');
        const values = [];
        let i = 0;
        while (i < value.length) {
          const bracketStart = value.indexOf('[');
          const bracketEnd = value.indexOf(']', bracketStart);

          if (bracketStart === -1 || bracketEnd === -1) break;

          // Check for nested brackets within the segment value
          let innerKey, innerValue;
          const nextBracket = value.indexOf('['), nextClose = value.indexOf(']', nextBracket + 1);
          if (nextBracket !== -1 && nextClose !== -1 && bracketEnd > 0) {
            // Nested key: extract from the part before this segment's closing bracket
            innerKey = decodeURIComponent(value.slice(0, bracketStart));
            innerValue = decodeURIComponent(value.slice(bracketEnd + 1, value.indexOf(']')));

            if (innerKey.endsWith('[]')) {
              const nestedValues = [];
              let j = 0;
              while (j < innerValue.length) {
                const nb = innerValue.indexOf('['), nc = innerValue.indexOf(']', nb + 1);
                if (nb === -1 || nc === -1) break;

                const innerNextBracket = innerValue.indexOf('['), innerNextClose = innerValue.indexOf(']', innerNextBracket + 1);
                if (innerNextBracket !== -1 && innerNextClose !== -1) {
                  nestedValues.push(decodeURIComponent(innerValue.slice(0, nb)));
                  innerKey = decodeURIComponent(innerValue.slice(nb + 1, innerNextBracket));
                  break;
                } else {
                  // Non-nested segment value (e.g., 'a')
                  const val = decodeURIComponent(value.slice(j, nextClose - 1));
                  nestedValues.push(val);
                }

                j = innerValue.indexOf(']', nb + 1);
              }
              currentKey = innerKey;
              currentValue = '[' + nestedValues.join(',') + ']';
            } else {
              // Nested array value (e.g., 'a,b')
              const arrVal = decodeURIComponent(innerValue.slice(0, bracketEnd));
              values.push(arrVal);
            }

            i += nextClose;
          } else if (bracketStart !== -1) {
            currentKey = key.replace(/(\[\])$/, '');
            value = decodeURIComponent(value.slice(bracketStart + 1, value.indexOf(']')));
            const arrVal = decodeURIComponent(value);
            values.push(arrVal);

            i += nextClose;
          } else {
            // Value without brackets (e.g., 'abc')
            currentKey = key;
            currentValue = decodeURIComponent(value);
            break;
          }

          i++;
        }
      } else if (currentKey === null) {
        // No '=' found, so the segment itself is a key with value 'true'
        currentKey = segment.replace(/(\[\])$/, '');
        currentValue = 'true';
      }
    }

    // If we have both a key and value, store the pair
    if (key !== null) {
      result[key] = currentValue;
      delete currentKey;
      delete currentValue;
    } else if (currentKey === null) {
      // Single segment like "b[]=x" -> no '=' found
      currentKey = '[]';
      currentValue = decodeURIComponent(value);
    }

    // If we have a key with array value, process it
    const arrIndex = result[key] ? [...result[key]].length : 0;
    if (arrIndex >= values.length) {
      break;
    }
    result[key][arrIndex] = currentValue;
  }

  return result;
}