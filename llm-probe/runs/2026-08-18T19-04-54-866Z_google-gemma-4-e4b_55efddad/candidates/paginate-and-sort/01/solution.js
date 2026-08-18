export function solve(input) {
    let items = [...(input?.items || [])];

    // 1. Filtering
    const filterCriteria = input?.filter;
    if (filterCriteria && items.length > 0) {
        const field = filterCriteria.field;
        const op = filterCriteria.op;
        const value = filterCriteria.value;

        items = items.filter(item => {
            let itemValue = item[field];
            let comparisonResult = false;

            if (typeof itemValue === 'undefined' || itemValue === null) {
                // Handle missing fields based on operator expectation
                if (op === 'eq') return value === undefined && itemValue === undefined;
                if (op === 'neq') return value !== undefined && (itemValue === undefined || itemValue === null);
                return false; // Cannot compare if field is missing for other ops.
            }

            try {
                switch (op) {
                    case 'eq':
                        comparisonResult = String(itemValue).toLowerCase() === String(value).toLowerCase();
                        break;
                    case 'neq':
                        comparisonResult = String(itemValue).toLowerCase() !== String(value).toLowerCase();
                        break;
                    case 'contains':
                        if (typeof itemValue === 'string' && typeof value === 'string') {
                            const searchString = value.toLowerCase();
                            const itemStr = itemValue.toLowerCase();
                            comparisonResult = itemStr.includes(searchString);
                        } else {
                            // Fallback for non-string types or missing values in contains check
                            const itemStrFallback = String(itemValue).toLowerCase();
                            const valueFallback = String(value).toLowerCase();
                            comparisonResult = itemStrFallback.includes(valueFallback);

                        }
                        break;
                    case 'gt':
                    case 'gte':
                    case 'lt':
                    case 'lte': {
                        // Attempt numeric comparison for reliable sorting/filtering results
                        const numA = parseFloat(itemValue);
                        const numB = parseFloat(value);

                        if (!isNaN(numA) && !isNaN(numB)) {
                            if (op === 'gt') return numA > numB;
                            if (op === 'gte') return numA >= numB;
                            if (op === 'lt') return numA < numB;
                            if (op === 'lte') return numA <= numB;
                        }
                        // Fallback to standard string comparison if numeric conversion fails or is inappropriate
                        const itemStr = String(itemValue).toLowerCase();
                        const valueStr = String(value).toLowerCase();

                        if (op === 'gt') return itemStr > valueStr;
                        if (op === 'gte') return itemStr >= valueStr;
                        if (op === 'lt') return itemStr < valueStr;
                        if (op === 'lte') return itemStr <= valueStr;

                    }
                }
            } catch (e) {
                // If comparison fails due to type error, treat it as non-match
                comparisonResult = false;
            }

            return comparisonResult;
        });
    }


    // 2. Sorting
    let sortedItems = items;
    const sortCriteria = input?.sort;

    if (sortCriteria && sortedItems.length > 0) {
        const field = sortCriteria.field;
        const dir = sortCriteria.dir === 'desc' ? -1 : 1;

        // Stable Sort implementation: Augment items with original index to break ties
        let indexedItems = sortedItems.map((item, index) => ({ item, originalIndex: index }));

        indexedItems.sort((a, b) => {
            const valA = a.item[field];
            const valB = b.item[field];

            // Primary comparison based on field value
            let primaryComparison;
            try {
                // Attempt numeric comparison first if values look like numbers
                const numA = parseFloat(valA);
                const numB = parseFloat(valB);
                if (!isNaN(numA) && !isNaN(numB)) {
                    primaryComparison = numA - numB;
                } else {
                    // Fallback to string comparison (case-insensitive)
                    const strA = String(valA).toLowerCase();
                    const strB = String(valB).toLowerCase();

                    if (strA < strB) primaryComparison = -1;
                    else if (strA > strB) primaryComparison = 1;
                    else primaryComparison = 0;
                }
            } catch (e) {
                 // Default to tie if comparison fails entirely
                primaryComparison = 0;
            }

            let sortResult;
            if (primaryComparison !== 0) {
                sortResult = primaryComparison * dir;
            } else {
                // Tie-breaker: Use original index for stable sort guarantee
                sortResult = (a.originalIndex - b.originalIndex);
            }
            return sortResult;
        });

        sortedItems = indexedItems.map(indexedItem => indexedItem.item);
    }


    // 3. Pagination
    const pageSize = input?.pageSize || 10;
    const page = Math.max(1, parseInt(input?.page) || 1); // Ensure page is at least 1

    const total = sortedItems.length;
    const totalPages = Math.ceil(total / pageSize);

    // Clamp current page if it exceeds available pages or is negative
    let effectivePage = Math.min(Math.max(page, 1), totalPages || (total > 0 ? 1 : 0));

    if (total === 0) {
        return { items: [], total: 0, page: 1, totalPages: 0 };
    }


    const startIndex = (effectivePage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, total);

    const paginatedItems = sortedItems.slice(startIndex, endIndex);

    return {
        items: paginatedItems,
        total: total,
        page: effectivePage,
        totalPages: totalPages
    };
}