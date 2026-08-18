export function solve(input) {
  const groups = {};
  
  for (const word of input.words) {
    const key = word.sort().join('');
    
    if (!groups[key]) {
      groups[key] = [];
    }
    
    groups[key].push(word);
  }

  const sortedGroups = Object.entries(groups).reduce((acc, [key, value]) => {
    acc[key] = [...value].sort();
    return acc;
  }, {});

  const sortedKeys = Object.keys(sortedGroups).sort();

  const result = {};
  
  for (const key of sortedKeys) {
    result[key] = sortedGroups[key];
  }

  return result;
}