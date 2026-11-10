async function pMap(items, mapper, options = { concurrency: 1 }) {
    const concurrency = typeof options === 'number' ? options : options.concurrency || 1;
    const retries = options.retries !== undefined ? options.retries : 0;
    const backoffMs = options.backoffMs !== undefined ? options.backoffMs : 0;
    const timeoutMs = options.timeoutMs !== undefined ? options.timeoutMs : 0;

    if (items.length === 0) return [];

    const results = new Array(items.length);
    let nextIndex = 0;
    const activeTasks = new Set();

    async function processNext() {
        if (nextIndex >= items.length || activeTasks.size >= concurrency) return Promise.resolve();

        try {
            const item = items[nextIndex];
            const attempt = async () => {
                const startTime = Date.now();
                let retryCount = 0;

                while (retryCount <= retries) {
                    if (timeoutMs > 0 && Date.now() - startTime >= timeoutMs) {
                        throw new Error("Timeout");
                    }

                    try {
                        const result = await Promise.race([
                            mapper(item, nextIndex),
                            new Promise((_, reject) =>
                                setTimeout(() => reject(new Error("Timeout")), timeoutMs)
                            )
                        ]);
                        results[nextIndex] = result;
                        return;
                    } catch (error) {
                        retryCount++;
                        if (retryCount > retries) throw error;

                        const delay = backoffMs * Math.pow(2, retryCount - 1);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }

                throw new Error("Max retries exceeded");
            };

            activeTasks.add(nextIndex);
            await attempt();
        } catch (error) {
            return Promise.reject(error);
        } finally {
            activeTasks.delete(nextIndex);
            nextIndex++;
            processNext();
        }
    }

    await processNext();
    return results;
}
