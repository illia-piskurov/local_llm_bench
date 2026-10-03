async function pMap(items, mapper, options = {}) {
  const { signal, settled = false } = options;
  if (signal && signal.aborted) {
    return Promise.reject(signal.reason || new Error("Aborted"));
  }

  const results = [];
  let index = 0;

  async function processItem(itemIndex) {
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 0));
      try {
        if (signal && signal.aborted) throw new Error("Aborted");
        const startTime = Date.now();
        const result = await Promise.race([
          mapper(items[index], index),
          new Promise((_, reject) =>
            setTimeout(reject, options.timeoutMs || Infinity, Error("Timeout"))
          ),
        ]);
        results.push({ status: "fulfilled", value: result });
        index++;
        return;
      } catch (error) {
        if (signal && signal.aborted) throw error;
        if (options.retries <= 0) {
          results.push({ status: "rejected", reason: error.message || error });
          index++;
          return;
        }
        const delay = options.backoffMs * Math.pow(2, options.retries - 1);
        await new Promise(resolve => setTimeout(resolve, delay));
        options.retries--;
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

  if (!settled) return results;
  const settledResults = [];
  while (results.length > 0) {
    const result = results.shift();
    settledResults.push(result.status === "fulfilled" ? { status: "fulfilled", value: result.value } : { status: "rejected", reason: result.reason });
    if (!settled && signal && signal.aborted) break;
  }
  return settled ? settledResults : results;
}
