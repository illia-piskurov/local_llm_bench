async function pMap(items, mapper, options) {
    if (!Array.isArray(items)) {
        throw new TypeError("Items must be an array.");
    }

    const N = items.length;
    if (N === 0) {
        return [];
    }

    // --- Option Parsing and Defaults ---
    let concurrencyLimit = 1;
    let retries = 0;
    let backoffMs = 0;
    let timeoutMs = 0;
    let signal = null;
    let settledMode = false;

    const getOptions = (opts) => {
        if (typeof opts === 'number' && Number.isInteger(opts) && opts > 0) {
            return { concurrency: Math.min(opts, N), retries: 0, backoffMs: 0, timeoutMs: 0, signal: null, settled: false };
        } else if (typeof opts === 'object' && opts !== null) {
            const limit = typeof opts.concurrency === 'number' ? Math.min(Math.max(1, opts.concurrency), N) : N;
            const r = Number.isInteger(opts.retries) && opts.retries >= 0 ? opts.retries : 0;
            const b = typeof opts.backoffMs === 'number' && opts.backoffMs >= 0 ? opts.backoffMs : 0;
            const t = typeof opts.timeoutMs === 'number' && opts.timeoutMs > 0 ? opts.timeoutMs : 0;
            const s = (opts.signal instanceof AbortSignal) ? opts.signal : null;
            const settled = typeof opts.settled === 'boolean';

            return { concurrency: limit, retries: r, backoffMs: b, timeoutMs: t, signal: s, settled: settled };
        }
        // Default case (options undefined/invalid)
        return { concurrency: 1, retries: 0, backoffMs: 0, timeoutMs: 0, signal: null, settled: false };
    };

    const opts = getOptions(options);
    concurrencyLimit = opts.concurrency;
    retries = opts.retries;
    backoffMs = opts.backoffMs;
    timeoutMs = opts.timeoutMs;
    signal = opts.signal;
    settledMode = opts.settled;


    // --- Helper Functions ---

    /** Creates a delay promise */
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    /** Executes the mapper with retries, backoff, timeout, and signal handling. */
    async function executeTaskWithRetryAndTimeout(item, index) {
        let lastError = null;
        let attempt = 0;

        while (attempt <= retries) {
            // Check for cancellation before starting the task
            if (signal && signal.aborted) {
                throw new DOMException("Aborted", "AbortError");
            }

            try {
                // 1. Timeout implementation setup
                const taskPromise = mapper(item, index);
                let timeoutPromise;
                if (timeoutMs > 0) {
                    timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error("Timeout")), timeoutMs)
                    );
                } else {
                    // If no timeout is set, use a promise that never rejects naturally.
                    timeoutPromise = Promise.resolve();
                }

                // Race the task against the timeout and the signal
                const racePromises = [taskPromise, timeoutPromise, new Promise((_, reject) => {
                    signal?.addEventListener('abort', () => reject(new DOMException("Aborted", "AbortError")), { once: true });
                })];

                // Wait for the first promise to resolve/reject
                const result = await Promise.race(racePromises);
                return result; // Success! Return the result immediately.

            } catch (e) {
                lastError = e;

                // Check if the error was due to cancellation or timeout, and handle retries accordingly.
                if ((signal && signal.aborted) || e.message === "Timeout" || e instanceof DOMException && e.code === 'AbortError') {
                    // If aborted/timed out, we treat it as a failure that might trigger retry logic, 
                    // unless the abort was permanent (i.e., triggered by Promise.race rejection).
                }

                attempt++;

                // Check for cancellation after catching an error
                if (signal && signal.aborted) {
                     throw e; // Propagate AbortError immediately if cancelled mid-retry cycle
                }


                // If this was the last attempt allowed, throw the error permanently.
                if (attempt > retries) {
                    const finalError = new Error(`Task failed after ${retries + 1} attempts for index ${index}. Last error: ${e.message}`);
                    throw finalError;
                }

                // Calculate backoff delay: base * 2^(attempt - 1)
                const delay = backoffMs * Math.pow(2, attempt - 1);
                console.warn(`Task failed at index ${index}. Retrying in ${delay}ms...`);
                await sleep(delay);
            }
        }
    }

    // --- Main Logic ---

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

        // Check for cancellation before starting the batch
        if (signal && signal.aborted) {
             throw new DOMException("Aborted", "AbortError");
        }

        const batchEnd = Math.min(currentIndex + concurrencyLimit, N);
        const tasksToRun = [];

        // Create promises for the current batch
        for (let i = currentIndex; i < batchEnd; i++) {
            tasksToRun.push((async () => {
                try {
                    // Execute the task with all retry/timeout logic built-in
                    const result = await executeTaskWithRetryAndTimeout(items[i], i);

                    if (settledMode) {
                        results[i] = { status: 'fulfilled', value: result };
                    } else {
                        results[i] = result;
                    }
                } catch (e) {
                    // If the error is an AbortError, we must re-throw it to trigger immediate rejection.
                    if ((signal && signal.aborted) || e instanceof DOMException && e.code === 'AbortError') {
                        throw e; 
                    }

                    // Handle permanent failure (after retries or non-cancellation error)
                    if (settledMode) {
                        results[i] = { status: 'rejected', reason: e };
                    } else {
                        // In non-settled mode, we re-throw to fail the entire pMap.
                        throw e; 
                    }
                }
            })());
        }

        currentIndex = batchEnd;

        let allSettledResults;
        if (settledMode) {
             // Use Promise.allSettled for settled mode
            allSettledResults = await Promise.allSettled(tasksToRun);
        } else {
            // In non-settled mode, we use Promise.all to fail fast on the first rejection.
            await Promise.all(tasksToRun);
            return; // If successful in non-settled mode, just return.
        }

        // If settledMode was true, we don't need to do anything with allSettledResults 
        // because results[i] was populated inside the async IIFE block above.
        
        // Recursively call processBatch to handle the next chunk of tasks
        return processBatch();
    }

    try {
        // Start the processing loop and wait for all batches to complete
        await processBatch();

        if (settledMode) {
            return results; // Return the structured result array
        } else {
            return results; // Return the raw value array
        }
    } catch (error) {
        // If the error is an AbortError, re-throw it to signal cancellation.
        if ((signal && signal.aborted) || error instanceof DOMException && error.code === 'AbortError') {
            throw error; 
        }
        // Otherwise, re-throw any other processing error (e.g., permanent task failure).
        throw error;
    }
}
