export function solve(input) {
  if (input === null || input === undefined) {
    return false;
  }

  if (typeof input === 'object' && input !== null && !Array.isArray(input)) {
    for (const key in input) {
      if (input.hasOwnProperty(key)) {
        solve(input[key]);
      }
    }
  } else if (typeof input === 'string') {
    return input;
  }

  return false;
}