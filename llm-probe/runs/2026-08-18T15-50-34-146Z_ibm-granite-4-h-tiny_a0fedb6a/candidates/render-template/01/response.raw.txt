export function solve(input) {
    const template = input.template;
    const data = input.data;

    const render = (value, path) => {
        const keys = path.split(".");
        let current = value;
        for (const key of keys) {
            if (current === undefined || current === null || !(key in current)) {
                return "";
            }
            current = current[key];
        }
        return String(current);
    };

    const renderString = (str, data) => {
        const placeholderRegex = /{{\s*([^}]+)\s*}}/g;
        let result = str;
        let match;
        while ((match = placeholderRegex.exec(str))) {
            const path = match[1];
            const replacement = render(data, path);
            result = result.replace(match[0], replacement);
        }
        return result;
    };

    return renderString(template, data);
}