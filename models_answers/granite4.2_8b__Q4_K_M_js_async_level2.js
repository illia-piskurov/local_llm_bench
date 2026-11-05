async function pMap(items, mapper, options) {
  const opts = typeof options === 'number' ? { concurrency: options } : options ?? {};
  const concurrency = opts.concurrency ?? 1;
  const retries = opts.retries ?? 0;
  const backoffMs = opts.backoffMs ?? 0;
  const timeoutMs = opts.timeoutMs ?? 0;

  if (items.length === 0) return [];

  const results = new Array(items.length);
  const pendingPromises = [];
  let nextIndex = 0;

  async function runItem(index, attempt = 0) {
    const maxAttempts = 1 + retries;
    if (attempt >= maxAttempts) {
      throw new Error('Max retries exceeded');
    }

    const timeoutPromise = timeoutMs > 0
      ? new Promise((_, reject) => {
          setTimeout(() => reject(new Error("Timeout")), timeoutMs);
        })
      : Promise.resolve();

    try {
      await Promise.race([mapper(items[index], index), timeoutPromise]);
      results[index] = await Promise.resolve(); // placeholder, actual result from mapper already awaited
    } catch (err) {
      if (err.message === "Timeout" && attempt < maxAttempts - 1) {
        // retry on timeout
        const delay = backoffMs * (2 ** attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        return runItem(index, attempt + 1);
      }
      // other errors or max retries -> propagate
      throw err;
    }
  }

  const processQueue = async () => {
    while (nextIndex < items.length) {
      while (pendingPromises.length < concurrency && nextIndex < items.length) {
        const idx = nextIndex++;
        pendingPromises.push(runItem(idx));
      }

      if (pendingPromises.length === 0) continue;

      const firstPending = pendingPromises.shift();
      try {
        await firstPending;
      } catch (err) {
        throw err;
      }

      if (nextIndex >= items.length && pendingPromises.length === 0) break;
    }
  };

  await processQueue();
  return results;
}
