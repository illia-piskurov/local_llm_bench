async function pMap(items, mapper, options) {
    if (!Array.isArray(items)) {
        throw new TypeError("Items must be an array.");
    }

    const N = items.length;
    if (N === 0) {
        return [];
    }

    // Determine concurrency limit
    let concurrencyLimit = 1;
    if (typeof options === 'number' && Number.isInteger(options) && options > 0) {
        concurrencyLimit = Math.min(options, N);
    } else if (typeof options === 'object' && options !== null && typeof options.concurrency === 'number') {
        const limit = options.concurrency;
        if (Number.isInteger(limit) && limit > 0) {
            concurrencyLimit = Math.min(limit, N);
        } else {
            throw new TypeError("Concurrency must be a positive integer.");
        }
    }

    // Array to hold the results in order
    const results = new Array(N);
    let currentIndex = 0;

    /**
     * Processes the next batch of tasks up to concurrencyLimit.
     * @returns {Promise<void>} A promise that resolves when all items are processed.
     */
    async function processBatch() {
        if (currentIndex >= N) {
            return Promise.resolve(); // All done
        }

        const batchEnd = Math.min(currentIndex + concurrencyLimit, N);
        const tasksToRun = [];

        // Create promises for the current batch
        for (let i = currentIndex; i < batchEnd; i++) {
            tasksToRun.push((async () => {
                try {
                    // Execute mapper and store result in the correct index slot
                    results[i] = await mapper(items[i], i);
                } catch (e) {
                    // Propagate error immediately upon rejection/exception
                    throw e; 
                }
            })());
        }

        currentIndex = batchEnd;

        // Wait for the current batch to complete. If any promise rejects, Promise.all will reject instantly.
        await Promise.all(tasksToRun);

        // Recursively call processBatch to handle the next chunk of tasks
        return processBatch();
    }

    try {
        // Start the processing loop and wait for all batches to complete
        await processBatch();
        return results;
    } catch (error) {
        // Re-throw any error encountered during mapping/processing
        throw error;
    }
}
