async function pMap(items, mapper, options) {
  const concurrency = typeof options === 'number' ? options : options?.concurrency ?? 1;
  if (items.length === 0) return [];

  const results = new Array(items.length);
  const pendingPromises = [];
  let nextIndex = 0;

  async function runItem(index) {
    try {
      const result = await mapper(items[index], index);
      results[index] = result;
    } catch (err) {
      throw err;
    }
  }

  const processQueue = async () => {
    while (nextIndex < items.length) {
      // Start up to concurrency tasks
      while (pendingPromises.length < concurrency && nextIndex < items.length) {
        const idx = nextIndex++;
        pendingPromises.push(runItem(idx));
      }

      // Wait for the next pending task to finish
      if (pendingPromises.length === 0) continue;

      const firstPending = pendingPromises.shift();
      try {
        await firstPending;
      } catch (err) {
        throw err;
      }

      // If all tasks done, exit
      if (nextIndex >= items.length && pendingPromises.length === 0) break;
    }
  };

  await processQueue();
  return results;
}
