async function pMap(items, mapper, options = {}) {
  const { retries = 0, backoffMs = 0, timeoutMs } = options;
  if (items.length === 0) return [];

  const results = new Array(items.length).fill(undefined);
  let index = 0;

  async function processItem(itemIndex) {
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 0));
      if (index >= items.length) break;
      try {
        const startTime = Date.now();
        results[index] = await Promise.race([
          mapper(items[index], index),
          new Promise((_, reject) =>
            setTimeout(reject, timeoutMs || Infinity, Error("Timeout"))
          ),
        ]);
        index++;
        return;
      } catch (error) {
        if (error.name === "Error" && error.message === "Timeout") throw error;
        if (retries <= 0) return Promise.reject(error);
        const delay = backoffMs * Math.pow(2, retries - 1);
        await new Promise(resolve => setTimeout(resolve, delay));
        retries--;
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
