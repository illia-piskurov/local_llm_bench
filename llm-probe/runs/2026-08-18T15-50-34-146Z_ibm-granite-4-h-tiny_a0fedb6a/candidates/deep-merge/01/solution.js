export function solve(input) {
  const merge = (target, source) => {
    for (const key in source) {
      if (source[key] === undefined) continue;
      if (
        typeof target[key] === "object" &&
        target[key] !== null &&
        !Array.isArray(target[key]) &&
        source[key] instanceof Object &&
        !(source[key] instanceof Array)
      ) {
        merge(target[key], source[key]);
      } else {
        target[key] = source[key];
      }
    }
  };

  let result = {};
  for (const obj of input.objects) {
    merge(result, obj);
  }
  return result;
}