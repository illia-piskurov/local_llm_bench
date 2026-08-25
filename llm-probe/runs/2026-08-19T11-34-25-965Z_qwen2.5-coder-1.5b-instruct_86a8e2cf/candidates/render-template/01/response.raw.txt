export function solve(input) { 
    let result = input.template;
    for (const [key, value] of Object.entries(input.data)) {
        const path = key.trim().split('.');
        let current = result;

        for (let i = 0; i < path.length - 1; i++) {
            if (!current[path[i]]) {
                current[path[i]] = {};
            }
            current = current[path[i]];
        }

        // Resolve the last part of the path
        const lastPart = path[path.length - 1];
        if (current[lastPart] === undefined || current[lastPart] === null) {
            continue; // Skip unresolved paths
        }

        if (typeof current[lastPart] !== 'string') {
            current[lastPart] = String(current[lastPart]);
        }
        
        result = current[lastPart].replace('{{', '').replace('}}', '');
    }
    
    return result;
}