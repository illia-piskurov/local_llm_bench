export function solve(input) {
  const words = Array.isArray(input?.words) ? [...input.words] : [];
  if (words.length === 0) return [];

  const groupsMap = new Map();

  for (const w of words) {
    const key = [...w].sort().join('');
    let arr = groupsMap.get(key);
    if (!arr) {
      arr = [];
      groupsMap.set(key, arr);
    }
    arr.push(w);
  }

  const result = Array.from(groupsMap.values()).map(group => {
    group.sort();
    return group;
  });

  result.sort((a, b) => a[0].localeCompare(b[0]));
  return result;
}