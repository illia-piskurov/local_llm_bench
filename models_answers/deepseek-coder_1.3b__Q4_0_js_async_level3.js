async function pMap(items, mapper, options = { concurrency: 1, signal: null, backoffMs: 0, timeoutMs: 0, settled: false }) {
    const concurrency = Math.min(options.concurrency, items.length);
    const results = [];
    const mapperWithIndex = (item, index) => mapper(item, index).catch(error => {
        throw error;
    });

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        let retryCount = 0;
        let backoff = options.backoffMs * (2 ** retryCount);
        const maxBackoff = options.timeoutMs ? options.timeoutMs : Infinity;
        const timeout = options.timeoutMs ? new Promise(resolve => setTimeout(resolve, options.timeoutMs)) : Promise.resolve();

        while (retryCount <= options.retries) {
            if (options.signal && options.signal.aborted) {
                if (options.settled) {
                    results.push({ status: 'rejected', reason: options.signal.reason });
                } else {
                    results.push({ status: 'rejected', reason: options.signal.reason || new Error("Aborted") });
                }
                break;
            }

            if (options.settled) {
                results.push(await Promise.race([mapperWithIndex(item, i), timeout]));
            } else {
                results.push(await Promise.race([mapperWithIndex(item, i), timeout]).catch(error => {
                    if (error.message === "Aborted") {
                        if (options.signal) {
                            options.signal.abort();
                        }
                        if (retryCount < options.retries) {
                            retryCount++;
                            backoff = Math.min(backoff * 2, maxBackoff);
                            await new Promise(resolve => setTimeout(resolve, backoff));
                        } else {
                            throw new Error("Timeout");
                        }
                    }
                });
            }
        }
    }

    return results;
}
