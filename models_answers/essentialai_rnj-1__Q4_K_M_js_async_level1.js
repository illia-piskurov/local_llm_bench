async function pMap(items, mapper, options) {
    if (!items || items.length === 0) return [];

    const concurrency = typeof options === 'number' ? options : (options && options.concurrency) || 1;
    const results = new Array(items.length);
    let activeCount = 0;

    async function processItem(index) {
        try {
            if (index >= items.length) return;
            const result = await mapper(items[index], index);
            results[index] = result;
            activeCount--;
            // Start next item processing
            for (let i = 0; i < concurrency && index + i < items.length; i++) {
                if (!results[index + i]) {
                    processItem(index + i).catch(err => { throw err; });
                    break;
                }
            }
        } catch (err) {
            // Reject immediately on any error
            return Promise.reject(err);
        }
    }

    for (let i = 0; i < concurrency && i < items.length; i++) {
        processItem(i).catch(err => { throw err; });
    }

    return new Promise((resolve, reject) => {
        const checkCompletion = () => {
            if (activeCount === 0 && results.every(result => result !== undefined)) {
                resolve(results);
            } else {
                setTimeout(checkCompletion, 100); // Polling for completion
            }
        };
        checkCompletion();
    });
}
