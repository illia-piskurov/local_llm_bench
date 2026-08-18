export function solve(input) {
  const words = input.words?.words || [];
  const anagramGroups = words.reduce((acc, word) => {
    const key = word.sort().join('');
    if (!acc[key]) acc[key] = [];
    acc[key].push(word);
    return acc;
  }, {});

  const sortedGroups = Object.keys(anagramGroups).map(key => 
    anagramGroups[key].sort().join('')
  );

  return sortedGroups.map(group => group.split(',').map(w => w.trim()).sort()).filter(g => g.length > 0);
}