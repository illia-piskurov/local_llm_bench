async function pMap(items, mapper, options) {
  if (!items || items.length === 0) {
    return [];
  }

  const concurrency = options?.concurrency ?? 1;
  const running = new Set();
  const results = new Array(items.length);
  let currentIndex = 0;

  return new Promise((resolve, reject) => {
    const executeTask = async (index, item) => {
      const timeoutMs = options?.timeoutMs ?? 0;
      let retries = options?.retries ?? 0;

      const attempt = async (retryNum) => {
        if (timeoutMs > 0) {
          const timeout = setTimeout(() => {
            console.log(`Task ${index} timed out after ${timeoutMs}ms`);
            running.delete(index);
            if (retries > 0) {
              retries--;
              setTimeout(() => attempt(retries + 1), options?.backoffMs ?? 0);
            } else {
              reject(new Error(`Task ${index} failed after ${retryNum} retries`));
            }
          }, timeoutMs);
          await Promise.race([mapper(item, index), timeout]);
          clearTimeout(timeout);
        } else {
          try {
            const result = await mapper(item, index);
            results[index] = result;
            running.delete(index);
            if (currentIndex < items.length) {
              executeTask(currentIndex, items[currentIndex]);
            }
            resolve(results);
          } catch (error) {
            if (retries > 0) {
              retries--;
              setTimeout(() => attempt(retries + 1), options?.backoffMs ?? 0);
            } else {
              reject(error);
            }
          }
        }
      };

      attempt(retries + 1);
    };

    for (let i = 0; i < items.length; i++) {
      executeTask(i, items[i]);
    }
  });
}
