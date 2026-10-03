async function pMap(items, mapper, options = {}) {
  const { concurrency } = typeof options === 'number' ? { concurrency: options } : options;
  if (items.length === 0) return [];

  const results = new Array(items.length).fill(undefined);
  let index = 0;

  async function processItem(itemIndex) {
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 0));
      if (index >= items.length) break;
      try {
        results[index] = await mapper(items[index], index);
        index++;
      } catch (error) {
        return Promise.reject(error);
      }
    }
  }

  const promises = [];
  while (index < items.length) {
    for (let i = 0; i < concurrency && index < items.length; i++) {
      promises.push(processItem(index));
    }
    await Promise.race(promises);
    promises.splice(0, promises.length);
  }

  return results;
}
