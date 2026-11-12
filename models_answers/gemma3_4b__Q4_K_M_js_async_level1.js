async function pMap(items, mapper, options) {
  if (!items || items.length === 0) {
    return [];
  }

  const concurrency = options?.concurrency ?? 1;
  const running = new Set();
  const results = new Array(items.length);
  let currentIndex = 0;

  return new Promise((resolve, reject) => {
    const executeTask = async () => {
      while (currentIndex < items.length) {
        const index = currentIndex++;
        const item = items[index];

        if (running.size < concurrency) {
          running.add(index);
          try {
            const result = await mapper(item, index);
            results[index] = result;
          } catch (error) {
            reject(error);
            return;
          } finally {
            running.delete(index);
            if (currentIndex < items.length) {
              executeTask();
            }
          }
        } else {
          // Wait for a task to complete
          await new Promise((resolve) => setTimeout(resolve, 0));
        }
      }

      resolve(results);
    };

    executeTask();
  });
}
