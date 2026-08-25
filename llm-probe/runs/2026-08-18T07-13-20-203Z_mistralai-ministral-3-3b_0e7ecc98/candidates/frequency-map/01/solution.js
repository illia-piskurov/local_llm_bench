export function solve(input) {
    const result = {};
    for (const item of input.items) {
        if (!result.hasOwnProperty(String(item))) {
            result[String(item)] = 0;
        }
        result[String(item)]++;
    }
    return result;
}