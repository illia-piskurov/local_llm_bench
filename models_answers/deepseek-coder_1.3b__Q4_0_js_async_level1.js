async function pMap(items, mapper, options = { concurrency: 1 }) {
    const concurrency = Math.min(options.concurrency, items.length);
    const results = [];
    const mapperWithIndex = (item, index) => mapper(item, index).catch(error => {
        throw error;
    });

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        results[i] = await Promise.race([
            mapperWithIndex(item, i),
            // If we're at the concurrency limit, we'll wait for the previous mapper to complete
            i < concurrency ? Promise.resolve() : results[i - 1]
        ]);
    }

    return results;
}
