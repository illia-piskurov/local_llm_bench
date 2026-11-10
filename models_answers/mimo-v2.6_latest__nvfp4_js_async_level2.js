async function pMap(items, mapper, options) {
  const opts = options === undefined || options === null
    ? {}
    : typeof options === 'number'
      ? { concurrency: options }
      : options;

  const concurrency = opts.concurrency ?? 1;
  const retries = opts.retries ?? 0;
  const backoffMs = opts.backoffMs ?? 0;
  const timeoutMs = opts.timeoutMs ?? 0;

  if (items.length === 0) {
    return [];
  }

  const results = new Array(items.length);
  let pending = 0;
  let nextIndex = 0;

  async function run() {
    while (pending < concurrency) {
      if (nextIndex >= items.length) {
        return;
      }

      const index = nextIndex++;
      pending++;

      const attempt = async () => {
        const promise = mapper(items[index], index);

        if (timeoutMs > 0) {
          const timer = new Promise((resolve) => {
            setTimeout(resolve, timeoutMs);
          });

          try {
            return await Promise.race([promise, timer.then(() => {
              throw new Error('Timeout');
            })]);
          } finally {
            clearTimeout(timer._id);
          }
        }

        return promise;
      };

      try {
        results[index] = await attempt();
      } catch (error) {
        if (retries > 0) {
          const delay = backoffMs * Math.pow(2, retries - 1);
          await new Promise((resolve) => setTimeout(resolve, delay));
          retries--;
          return attempt();
        }
        pending--;
        throw error;
      }

      pending--;
    }
  }

  await Promise.all(Array.from({ length: items.length }, (_, i) => run()));
  return results;
}
