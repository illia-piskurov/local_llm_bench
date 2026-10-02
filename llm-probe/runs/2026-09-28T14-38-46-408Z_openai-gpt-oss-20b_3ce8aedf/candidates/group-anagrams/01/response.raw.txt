export function solve(input) {
  const words = input.words.slice();
  const map = new Map();
  for (const w of words) {
    const key = [...w].sort().join('');
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(w);
  }
  const groups = [];
  for (const arr of map.values()) {
    groups.push(arr.sort());
  }
  groups.sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
  return groups;
}