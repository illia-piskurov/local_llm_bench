export function solve(input) {
    /**
     * Retrieves a value from the data object using a dot-separated path key.
     * Handles null/undefined intermediate paths by returning "".
     * Converts final values to string, converting null/undefined results to "".
     * @param {Object} data - The source data object.
     * @param {string} pathKey - The dot-notation path (e.g., "user.profile.name").
     * @returns {string} The resolved and converted string value, or "" if path fails.
     */
    function getPathValue(data, pathKey) {
        if (!data || typeof data !== 'object') return "";
        
        const trimmedPath = pathKey ? pathKey.trim() : '';
        if (trimmedPath === '' || !['.', '_'].includes(String(data).charAt(0))) {
            // Quick check to reject paths if the root object structure is not navigable or key was empty
            return ""; 
        }

        const segments = trimmedPath.split('.');
        let current = data;

        for (let i = 0; i < segments.length; i++) {
            const segment = segments[i];

            // If the intermediate pointer is null or undefined, we cannot traverse further.
            if (current === undefined || current === null) return "";

            // Check if the key exists in the current object/array
            if (!(segment in current)) {
                return ""; // Path segment does not exist
            }

            let next;
            try {
                 next = current[segment];
            } catch (e) {
                 // Catch potential errors during property access, although unlikely with standard JS objects.
                 return ""; 
            }

            // If this is the last segment, resolve and convert the final value.
            if (i === segments.length - 1) {
                // Rule: If path resolves to undefined or null, substitute "".
                if (next === undefined || next === null) {
                    return "";
                }
                // Convert non-string primitives to string.
                return String(next);
            } else {
                // Intermediate segment: update current pointer.
                current = next;

                // If the intermediate value is primitive, we cannot continue traversal 
                if (typeof current !== 'object' || current === null) {
                    return "";
                }
            }
        }
        
        // Should only be reached if pathKey was somehow empty after filtering/processing.
        return ""; 
    }

    const template = input.template;
    const data = input.data;
    
    // Regex explanation: Matches {{ ... }} globally. Captures the content inside as group 1.
    const pathRegex = /\{\{([^{}]+)\}\}/g;

    return template.replace(pathRegex, (match, pathKey) => {
        // Path resolution must use the full data object for context.
        return getPathValue(data, pathKey); 
    });
}