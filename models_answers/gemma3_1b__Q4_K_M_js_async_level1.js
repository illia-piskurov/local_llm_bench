async function pMap(items, mapper, options) {
  if (!items || items.length === 0) {
    return [];
  }

  const concurrency = options === undefined ? 1 : options;
  const results = [];

  for (let i = 0; i < items.length; i++) {
    try {
      const result = await mapper(items[i], i);
      results.push(result);
    } catch (error) {
      throw error;
    }
  }

  return results;
}
