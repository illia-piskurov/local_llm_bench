async function pMap(items, mapper, options = { concurrency: 1 }) {
    const concurrency = typeof options === 'number' ? options : options.concurrency || 1;
    const results = new Array(items.length);
    let nextIndex = 0;

    async function processNext() {
        if (nextIndex >= items.length) return Promise.resolve();

        const item = items[nextIndex];
        try {
            const result = await mapper(item, nextIndex);
            results[nextIndex] = result;
            nextIndex++;
            processNext();
        } catch (error) {
            throw error;
        }
    }

    await processNext();
    return results;
}
