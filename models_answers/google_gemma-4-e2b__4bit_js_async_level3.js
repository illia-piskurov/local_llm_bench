async function pMap(items, mapper, options) {
    if (!items || items.length === 0) {
        return [];
    }

    const concurrency = options !== undefined ? options.concurrency : 1;
    if (concurrency <= 0) {
        throw new Error("Concurrency limit must be a positive number.");
    }

    const retries = options?.retries ?? 0;
    const backoffMs = options?.backoffMs ?? 0;
    const timeoutMs = options?.timeoutMs ?? 0;
    const signal = options?.signal;
    const settled = options?.settled ?? false;

    // --- Abort Signal Handling ---
    if (signal) {
        if (signal.aborted) {
            return Promise.reject(new Error("Aborted"));
        }

        // Setup listener to handle abortion globally
        const abortHandler = () => {
            // Ensure that if we are mid-flight, the main promise is rejected immediately
            if (!signal.aborted) {
                signal.aborted = true; // Mark as handled
                // Propagate the rejection immediately outside this scope (if applicable)
            }
        };

        signal.addEventListener('abort', abortHandler, { once: true });
    }


    // Helper function to enforce a timeout on an async operation
    const withTimeout = (promise, ms) => {
        if (ms === 0) return promise;
        return new Promise((_, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error("Timeout"));
            }, ms);
            promise.then(
                (value) => {
                    clearTimeout(timeout);
                    return value;
                },
                (error) => {
                    clearTimeout(timeout);
                    return Promise.reject(error);
                }
            );
        });
    };

    // Core function to handle mapping with retries and timeouts
    const attemptMapping = async (index, item) => {
        let attempts = 0;

        while (attempts <= retries) {
            try {
                const mappingPromise = mapper(item, index);

                // Apply timeout if specified
                const result = await withTimeout(mappingPromise, timeoutMs);

                return { index, value: result }; // Success
            } catch (error) {
                attempts++;

                if (attempts > retries) {
                    // Final failure
                    throw error;
                }

                // Calculate exponential backoff delay
                const delay = backoffMs * Math.pow(2, attempts - 1);

                // Wait for the specified delay before retrying
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    };

    const results = new Array(items.length);
    const runningPromises = new Set();
    const promiseQueue = [];

    for (let i = 0; i < items.length; i++) {
        const item = items[i];

        // Define the task function that includes retry logic
        const task = async () => {
            return attemptMapping(i, item);
        };

        // Add the task to the queue
        promiseQueue.push(task());

        if (runningPromises.size < concurrency) {
            const taskRunner = promiseQueue.shift();

            const executionPromise = (async () => {
                try {
                    // Execute the task and await its result
                    const taskResult = await taskRunner();

                    return { status: 'fulfilled', value: taskResult };

                } catch (error) {
                    // Handle final failure / rejection
                    return { status: 'rejected', reason: error };
                } finally {
                    // Ensure the promise is removed from the running set regardless of success/failure
                    runningPromises.delete(executionPromise);
                }
            })();

            runningPromises.add(executionPromise);
        }

        // If the concurrency limit is reached, wait for a running promise to finish
        while (runningPromises.size >= concurrency) {
            // Wait for any running promise to complete before adding a new one.
            await Promise.race(Array.from(runningPromises));
        }
    }

    // Wait for all remaining promises in the queue to complete
    const finalResults = await Promise.all(promiseQueue);

    // If cancelled, the global listener would have rejected the top-level promise before this point
    return finalResults;
}
