async function pMap(items, mapper, options = { concurrency: 1 }) {
    const concurrency = typeof options === 'number' ? options : options.concurrency || 1;
    const retries = options.retries !== undefined ? options.retries : 0;
    const backoffMs = options.backoffMs !== undefined ? options.backoffMs : 0;
    const timeoutMs = options.timeoutMs !== undefined ? options.timeoutMs : 0;

    if (items.length === 0) return [];

    const results = new Array(items.length);
    let nextIndex = 0;
    const activeTasks = new Set();
    const semaphore = new Promise((resolve) => setTimeout(resolve, 0));

    async function processNext() {
        if (nextIndex >= items.length || activeTasks.size >= concurrency) return;

        const item = items[nextIndex];
        try {
            const controller = new AbortController();
            const timeoutId = timeoutMs > 0 ? setTimeout(() => controller.abort(), timeoutMs) : null;
            const taskPromise = mapper(item, nextIndex)
                .then(result => {
                    clearTimeout(timeoutId);
                    results[nextIndex] = result;
                    return Promise.resolve();
                })
                .catch(error => {
                    if (error.name === 'AbortError') throw new Error("Timeout");
                    activeTasks.delete(taskPromise);
                    throw error;
                });

            const taskPromiseWithRetry = async () => {
                let attempt = 0;
                while (attempt <= retries) {
                    try {
                        await taskPromise;
                        return;
                    } catch (error) {
                        if (attempt === retries) throw error;

                        const delay = backoffMs * Math.pow(2, attempt);
                        await new Promise(resolve => setTimeout(resolve, delay));
                        attempt++;
                    }
                }
            };

            activeTasks.add(taskPromiseWithRetry());
            taskPromiseWithRetry().finally(() => {
                clearTimeout(timeoutId);
                activeTasks.delete(taskPromiseWithRetry());
                nextIndex++;
                processNext();
            });
        } catch (error) {
            throw error;
        }
    }

    await processNext();
    return results;
}
