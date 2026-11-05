async function pMap(items, mapper, options = undefined) {
  if (!Array.isArray(items) || items.length === 0) return [];

  const concurrency = typeof options === 'number' ? options : (options || 1);
  const results = new Array(items.length);
  const pending = new Map(); // task id -> {item, index, promise}

  async function runTask(task) {
    try {
      const result = await mapper(task.item, task.index);
      results[task.index] = result;
    } catch (err) {
      throw err;
    }
  }

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const task = { item, index: i };
    pending.set(i, task);
    runTask(task).then(runTask);
  }

  // Worker pool loop
  while (pending.size > 0) {
    const task = pending.get(pending.keys().next().value);
    if (!task) break;
    pending.delete(task.index);
    const promise = runTask(task);
    if (pending.size === concurrency) {
      await promise;
    } else {
      pending.set(task.index, task);
    }
  }
  return results;
}
