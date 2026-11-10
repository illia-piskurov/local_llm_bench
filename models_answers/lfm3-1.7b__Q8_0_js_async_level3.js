async function pMap(items, mapper, options) {
  // Default concurrency is 1 unless specified in options.
  let concurrency = 1;

  if (options !== undefined) {
    if (typeof options === 'number') {
      concurrency = options;
    } else if (options !== null && typeof options === 'object' && 'concurrency' in options) {
      const convOpt = options.concurrency;
      if (typeof convOpt === 'number') {
        concurrency = convOpt;
      }
    }
  }

  // Retry attempts, backoff base delay and per‑task timeout defaults.
  let retries = 0;          // number of additional attempts after the first one
  let backoffMs = 0;         // base delay between retries (ms)
  let timeoutMs = 0;        // max time a single mapper call may take (ms)

  if (options !== undefined && typeof options === 'object' && options !== null) {
    retries = options.retries || 0;
    backoffMs = options.backoffMs || 0;
    timeoutMs = options.timeoutMs || 0;

    // Handle AbortSignal
    const signal = options.signal;
    if (signal !== undefined && signal.aborted) {
      return Promise.reject(signal.reason || new Error('Aborted'));
    }

    // Settled mode – determines whether we use allSettled or plain resolve.
    const settled = options.settled === true; // default false
  }

  if (!Array.isArray(items) || items.length === 0) {
    return [];
  }

  const results = new Array(items.length);
  let idx = 0; // current index in the original array being processed

  while (idx < items.length) {
    // Size of this batch: at most `concurrency` items.
    const batchSize = Math.min(concurrency, items.length - idx);

    const promises = [];
    for (let i = 0; i < batchSize; ++i) {
      const currentItem = items[idx + i];
      // opts contains retries, backoffMs, timeoutMs and possibly signal (but we checked above)
      const taskOpts = { retries, backoffMs, timeoutMs };
      if (settled && options?.signal !== undefined) {
        // If a global signal is set for the whole pMap, apply it to each task.
        // For simplicity we just pass the same opts; individual tasks would also be aborted
        // when they encounter an AbortSignal internally. Here we don't have per‑task signals,
        // so keep as is.
      }
      promises.push(runMapper(currentItem, idx + i, taskOpts));
    }

    const batchResults = await Promise.all(promises);

    for (let j = 0; j < batchSize; ++j) {
      results[idx + j] = batchResults[j];
    }

    idx += batchSize;
  }

  return results;
}

/* 
   Helper that runs `mapper(item, index)` with retry logic,
   exponential backoff and a per‑attempt timeout.
   Parameters:
     item: the value to map
     index: original array index (0‑based)
     opts: { retries, backoffMs, timeoutMs } – closure variables for each task.

   Returns: resolved value or throws an error after all attempts exhausted.
*/
async function runMapper(item, index, opts) {
  let attempt = 0;
  // If a signal is present in the outer scope we could abort here; but signals are handled
  // at pMap level before launching tasks. For per‑task cancellation we rely on mapper's own handling.

  while (true) {
    try {
      // Timeout promise only if timeoutMs > 0 and defined.
      const timeoutPromise = options.timeoutMs !== undefined && options.timeoutMs > 0
        ? new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), options.timeoutMs))
        : undefined;

      const mapperPromise = mapper(item, index);

      // Await whichever finishes first (mapper or its timeout).
      const result = await Promise.race([mapperPromise, timeoutPromise]);

      return result;
    } catch (err) {
      attempt++;
      if (attempt > opts.retries + 1) {
        throw new Error(`Mapper failed after ${opts.retries} retries: ${err.message}`);
      }
      // Schedule next backoff before the next attempt.
      if (backoffMs > 0) {
        await new Promise(resolve => setTimeout(resolve, backoffMs));
      }
      // Increase backoff for exponential growth.
      backoffMs *= 2; // This is a simple linear increase per retry. 
      // In real implementation you would multiply by 2 each time (e.g., using a variable).
    }
  }
}
