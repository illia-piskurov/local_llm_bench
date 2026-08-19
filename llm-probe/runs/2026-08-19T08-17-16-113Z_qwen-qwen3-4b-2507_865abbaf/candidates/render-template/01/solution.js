export function solve(input) {
    const template = input.template;
    const data = input.data || {};
    
    function resolvePath(path, obj) {
        if (!path) return "";
        
        const parts = path.split('.');
        let current = obj;
        
        for (let part of parts) {
            if (current === undefined || current === null) {
                return "";
            }
            
            // Handle array access (e.g. items.0)
            if (part.startsWith('0') || part.startsWith('1') || part.startsWith('2') || 
                part.startsWith('3') || part.startsWith('4') || part.startsWith('5') || 
                part.startsWith('6') || part.startsWith('7') || part.startsWith('8') || 
                part.startsWith('9')) {
                const index = parseInt(part);
                if (Array.isArray(current)) {
                    if (index >= 0 && index < current.length) {
                        current = current[index];
                    } else {
                        current = undefined;
                    }
                } else {
                    current = undefined;
                }
            } else {
                current = current[part];
            }
            
            if (current === undefined || current === null) {
                return "";
            }
        }
        
        // Convert non-string primitives to strings
        if (typeof current === 'number') return current.toString();
        if (typeof current === 'boolean') return current.toString();
        if (typeof current === 'object' && current !== null) return JSON.stringify(current);
        
        return current;
    }
    
    let result = template;
    const regex = /\{\{(\s*([^{}]*)\s*)\}\}/g;
    
    let match;
    while ((match = regex.exec(template)) !== null) {
        const path = match[2].trim();
        if (!path) continue;
        
        const value = resolvePath(path, data);
        result = result.replace(new RegExp(`{{\\s*${path}\\s*}}`, 'g'), value);
    }
    
    return result;
}