async function pMap(items, mapper, options = { concurrency: 1 }) {
  if (items.length === 0) return [];

  const results = new Array(items.length);
  let index = 0;

  const promises = [];

  for (let i = 0; i < items.length; i++) {
    promises.push(mapper(items[i], i));
  }

  for (const promise of promises) {
    promise.then((result) => {
      results[index++] = result;
    }).catch((error) => {
      if (options.signal.aborted) {
        if (options.retries > 0) {
          options.retries--;
          return pMap(items, mapper, options);
        }

        throw error;
      }

      if (options.settled) {
        options.settled = false;
        return Promise.allSettled(promises);
      }

      throw error;
    }).finally(() => {
      if (options.timeoutMs > 0) {
        const timeout = setTimeout(() => {
          throw new Error("Timeout");
        }, options.timeoutMs);
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve();
          }, options.backoffMs * Math.pow(2, options.retries));
        });
      }
    });
  }

  return Promise.allSettled(results.slice(0, options.concurrency));
}
