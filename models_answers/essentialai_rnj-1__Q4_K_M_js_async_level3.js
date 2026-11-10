async function pMap(items, mapper, options) {
    if (!items || items.length === 0) return [];

    const concurrency = typeof options === 'number' ? options : (options && options.concurrency) || 1;
    const retries = options && options.retries !== undefined ? options.retries : 0;
    const backoffMs = options && options.backoffMs !== undefined ? options.backoffMs : 0;
    const timeoutMs = options && options.timeoutMs !== undefined ? options.timeoutMs : 0;
    const signal = options && options.signal || null;
    const settled = options && options.settled === true;

    if (signal && signal.aborted) {
        return Promise.reject(signal.reason || new Error("Aborted"));
    }

    const results = new Array(items.length);
    let activeCount = 0;
    let isRejected = false;

    async function processItem(index, attempt = 0) {
        if (index >= items.length || isRejected) return;

        try {
            // Create a timeout promise
            const timeoutPromise = timeoutMs > 0 ? 
                new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), timeoutMs)) :
                Promise.resolve();

            // Run the mapper with timeout and signal handling
            const result = await Promise.race([mapper(items[index], index), timeoutPromise]);

            if (signal && signal.aborted) {
                isRejected = true;
                return Promise.reject(signal.reason || new Error("Aborted"));
            }

            results[index] = settled ? { status: 'fulfilled', value: result } : result;
            activeCount--;
        } catch (err) {
            if (attempt < retries && !isRejected) {
                // Retry with exponential backoff
                const delay = backoffMs * (2 ** attempt);
                await new Promise(resolve => setTimeout(resolve, delay));
                return processItem(index, attempt + 1);
            }
            if (!settled || isRejected) {
                isRejected = true;
                return Promise.reject(err);
            } else {
                results[index] = { status: 'rejected', reason: err };
                activeCount--;
            }
        }

        // Start next item processing if there are still items to process and concurrency allows
        for (let i = 0; i < concurrency && index + i < items.length; i++) {
            if (!results[index + i]) {
                processItem(index + i).catch(err => { throw err; });
                break;
            }
        }
    }

    // Initial processing of the first `concurrency` number of items
    for (let i = 0; i < concurrency && i < items.length; i++) {
        processItem(i).catch(err => { isRejected = true; return Promise.reject(err); });
    }

    return new Promise((resolve, reject) => {
        const checkCompletion = () => {
            if (activeCount === 0) {
                if (isRejected && !settled) {
                    // If any task failed and settled mode is off, reject with the first error
                    for (let i = 0; i < results.length; i++) {
                        if (!results[i]) continue;
                        const result = results[i];
                        if (result instanceof Error || (typeof result === 'object' && result.status === 'rejected')) {
                            return reject(result.reason || new Error("Task failed"));
                        }
                    }
                }
                resolve(results);
            } else {
                setTimeout(checkCompletion, 100); // Polling for completion
            }
        };
        checkCompletion();
    });
}
