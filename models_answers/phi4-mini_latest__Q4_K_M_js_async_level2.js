async function pMap(items, mapper, options = { concurrency: 1, retries: 0, backoffMs: 0, timeoutMs: 0 }) {
  const { concurrency, retries = 0, backoffMs = 0, timeoutMs = 0 } = options;
  if (items.length === 0) return [];
  const results = new Array(items.length);
  const executing = new Set();
  const queue = [];
  let attempt = 0;

  const enqueue = (index) => {
    if (index < items.length) {
      queue.push(index);
    }
  };

  const processNext = async () => {
    while (queue.length && executing.size < concurrency) {
      const currentIndex = queue.shift();
      executing.add(currentIndex);
      const attemptCurrent = ++attempt;
      const executeMapper = async () => {
        try {
          const startTime = Date.now();
          const result = await Promise.race([
            mapper(items[currentIndex], currentIndex, () => {
              executing.delete(currentIndex);
              enqueue(currentIndex + 1);
              if (currentIndex === items.length - 1) {
                enqueue(currentIndex + 1);
              }
            }),
            new Promise((resolve, reject) => {
              const timeout = setTimeout(() => reject(new Error("Timeout")), timeoutMs);
              process.nextTick(() => clearTimeout(timeout));
              const timer = setTimeout(() => reject(new Error("Timeout")), timeoutMs);
              process.nextTick(() => clearTimeout(timer));
            })
          ]);
          const endTime = Date.now();
          if (endTime - startTime > timeoutMs) {
            throw new Error("Timeout");
          }
          results[currentIndex] = result;
        } catch (error) {
          if (attemptCurrent <= retries + 1) {
            const delay = backoffMs * Math.pow(2, attemptCurrent - 1);
            await new Promise(resolve => setTimeout(resolve, delay));
            processNext();
          } else {
            throw error;
          }
        } finally {
          executing.delete(currentIndex);
          enqueue(currentIndex + 1);
        }
      };
      await executeMapper();
    }
  };

  enqueue(0);
  processNext();

  return new Promise((resolve, reject) => {
    const cleanup = () => {
      while (executing.size) {
        processNext();
      }
      process.nextTick(cleanup);
    };

    const wrappedProcessNext = async () => {
      try {
        await processNext();
        resolve(results);
      } catch (error) {
        reject(error);
      }
    };

    cleanup();
    return wrappedProcessNext();
  });
}
