async function pMap(items, mapper, options = { concurrency: 1 }) {
    const concurrency = typeof options === 'number' ? options : options.concurrency || 1;
    const retries = options.retries !== undefined ? options.retries : 0;
    const backoffMs = options.backoffMs !== undefined ? options.backoffMs : 0;
    const timeoutMs = options.timeoutMs !== undefined ? options.timeoutMs : 0;
    const signal = options.signal || (options.abortSignal ? options.abortSignal : new AbortController().signal);
    const settled = typeof options === 'object' && options.settled !== undefined ? options.settled : false;

    if (!signal.aborted) {
        const controller = new AbortController();
        signal.addEventListener('abort', () => controller.abort());
        signal = controller.signal;
    }

    if (items.length === 0 || signal.aborted) return settled
        ? items.map(() => ({ status: 'rejected', reason: signal.reason || "Aborted" }))
        : [];

    const results = new Array(items.length);
    let nextIndex = 0;
    const activeTasks = new Set();
    const failedIndices = new Set();

    async function processNext() {
        if (nextIndex >= items.length || activeTasks.size >= concurrency) return Promise.resolve();

        try {
            const item = items[nextIndex];
            const attempt = async () => {
                const startTime = Date.now();
                let retryCount = 0;

                while (retryCount <= retries && !signal.aborted) {
                    if (timeoutMs > 0 && Date.now() - startTime >= timeoutMs) {
                        throw new Error("Timeout");
                    }

                    try {
                        const result = await Promise.race([
                            mapper(item, nextIndex),
                            signal.promise.then(() => { throw signal.reason || new Error("Aborted"); }),
                            new Promise((_, reject) =>
                                setTimeout(() => reject(new Error("Timeout")), timeoutMs)
                            )
                        ]);
                        results[nextIndex] = result;
                        return;
                    } catch (error) {
                        retryCount++;
                        if (retryCount > retries || signal.aborted) throw error;

                        const delay = backoffMs * Math.pow(2, retryCount - 1);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }

                throw new Error("Max retries exceeded");
            };

            activeTasks.add(nextIndex);
            await attempt();
        } catch (error) {
            if (!settled || signal.aborted) return Promise.reject(error);
            results[nextIndex] = { status: 'rejected', reason: error.message };
        } finally {
            if (!signal.aborted && !failedIndices.has(nextIndex)) {
                activeTasks.delete(nextIndex);
                nextIndex++;
                processNext();
            }
        }
    }

    await processNext();

    // Cancel remaining tasks if signal was aborted
    if (signal.aborted) {
        return settled ? items.map(() => ({ status: 'rejected', reason: signal.reason || "Aborted" })) : [];
    }

    return results;
}
