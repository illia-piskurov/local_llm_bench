export function solve(input) {
    const template = input.template;
    const data = input.data;

    if (!template || !data) {
        return template || "";
    }

    // Regex to find placeholders: matches {{...}} and captures the content inside (non-greedy match)
    // The pattern handles optional whitespace inside the braces due to the capture group matching anything between the braces.
    const regex = /\{\{\s*(.*?)\s*\}\}/g;

    const processedTemplate = template.replace(regex, (match, path) => {
        // Trim path just in case, although the regex should handle internal spacing correctly based on rules.
        const trimmedPath = path.trim();
        if (!trimmedPath) {
            return "";
        }

        const parts = trimmedPath.split('.');
        let currentValue = data;
        let foundPath = true;

        // Resolve the nested path
        for (const part of parts) {
            if (currentValue === undefined || currentValue === null) {
                foundPath = false;
                break;
            }
            currentValue = currentValue[part];
        }

        if (!foundPath || currentValue === undefined || currentValue === null) {
            return "";
        }

        // Convert the resolved value to string (handles numbers, booleans, etc.)
        return String(currentValue);
    });

    return processedTemplate;
}