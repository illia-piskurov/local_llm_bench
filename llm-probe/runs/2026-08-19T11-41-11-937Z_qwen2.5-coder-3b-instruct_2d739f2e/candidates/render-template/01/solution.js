export function solve(input) {
    const { template, data } = input;
    
    // Helper function to get value from object using path
    const getValueFromPath = (obj, path) => {
        const keys = path.split('.');
        let current = obj;

        for (const key of keys) {
            if (!(key in current)) return '';
            current = current[key];
        }

        // Convert non-string values to string
        if (typeof current !== 'string') {
            current = String(current);
        }

        return current;
    };

    // Replace {{path}} placeholders with corresponding data values
    let result = template.replace(/{{\s*(.*?)\s*}}/g, (match, path) => {
        return getValueFromPath(data, path.trim());
    });

    return result;
}