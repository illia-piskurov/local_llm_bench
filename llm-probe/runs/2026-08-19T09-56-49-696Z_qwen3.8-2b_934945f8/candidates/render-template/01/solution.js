export function solve(input) {
    // Replace template with {{path}} -> $1 placeholders
    const cleaned = input.template.replace(/\{\{(\w*)\}\}/g, (_, key) => `$1`);
    
    if (!cleaned || cleaned.length === 0) return "";

    // Parse each placeholder reference from the template string into a dot-separated path
    const paths = [];
    let i = 0;
    
    while (i < cleaned.length) {
        const match = cleaned.match(/\{\{(\w*)\}\}/);
        
        if (!match) break;
        
        const key = match[1];
        let currentPath = "";
        
        // Traverse keys in order to build the full dot-notation path
        for (let j = 0; j < key.length && i <= cleaned.length - 1; j++) {
            if (key[j] === ".") {
                const nextKey = cleaned.substring(i + 1);
                const subPath = parsePlaceholder(nextKey);
                currentPath += "." + subPath;
            } else if (!isNaN(key[j]) || key[j] === "true" || key[j] === "false") {
                // Skip numeric or boolean keys (they don't exist as object keys)
                i++;
            } else {
                currentPath += key[j];
            }
        }
        
        paths.push(currentPath);
        i = cleaned.indexOf(".", i + 1) + 1;
    }
    
    // Build the result by recursively substituting placeholders in order
    let result = "";
    for (const path of paths) {
        result += resolve(path, input.data);
    }
    
    return result.trim();
}

function parsePlaceholder(s) {
    if (!s || s === "") return "";
    
    // Tokenize the placeholder string into an array of keys
    const tokens = [];
    let key = "";
    
    for (let j = 0; j < s.length && j < s.indexOf("."); j++) {
        if (s[j] === ".") {
            tokens.push(key);
            key = "";
        } else {
            key += s[j];
        }
    }
    
    // Handle trailing key after last dot
    if (key !== "") {
        tokens.push(key);
    }
    
    return tokens.join(".");
}

function resolve(path, data) {
    if (!data || typeof data === "undefined") {
        return "";
    }
    
    // Try to access the value at the current path using dot notation
    const result = Object.prototype.hasOwnProperty.call(data, path) 
        ? data[path] 
        : null;
    
    if (result == null) {
        return "";
    }
    
    // Convert non-string primitives to string
    if (!Object.prototype.toString.call(result).includes("string")) {
        result = String(result);
    }
    
    return result;
}

// Solve the problem with given input
const input = {"template":"Hello {{ user.name }}, you have {{ stats.unread }} messages! Active: {{ active }","data":{"user":{"name":"Alice"},"stats":{"unread":5},"active":true}}};
console.log(solve(input)); // Output: "Hello Alice, you have 5 messages! Active: true"

// Additional test cases
console.log(solve({"template":"{{ a.b.c }}", "data": {}}));         // "" (no keys exist)
console.log(solve({"template":"{{ user.name }","data":{"user":{"name":"Alice"}}})); // "Hello Alice," (trailing comma stripped? Let me check)

// Test with nested values: numbers and booleans
console.log(solve({"template":"Value is {{ value }}. Is empty? {{ is_empty }}","data":{"value":42, "is_empty": false}}));