export function solve(input) {
    const { schema, data } = input;
    let valid = true;
    const errors = {};

    for (const [field, rule] of Object.entries(schema)) {
        if (!(field in data)) {
            if (rule.required) {
                errors[field] = ['Required'];
                valid = false;
                continue;
            }
            continue;
        }

        const value = data[field];

        switch (rule.type) {
            case 'string':
                if (typeof value !== 'string') {
                    errors[field] = ['Invalid type'];
                    valid = false;
                } else if (rule.min && value.length < rule.min) {
                    errors[field] = ['Too short'];
                } else if (rule.max && value.length > rule.max) {
                    errors[field] = ['Too long'];
                }
                break;

            case 'number':
                if (typeof value !== 'number' || isNaN(value)) {
                    errors[field] = ['Invalid type'];
                    valid = false;
                } else if (rule.min && value < rule.min) {
                    errors[field] = ['Too small'];
                } else if (rule.max && value > rule.max) {
                    errors[field] = ['Too large'];
                }
                break;

            case 'boolean':
                if (typeof value !== 'boolean') {
                    errors[field] = ['Invalid type'];
                    valid = false;
                }
                break;

            case 'array':
                if (!Array.isArray(value)) {
                    errors[field] = ['Invalid type'];
                    valid = false;
                } else if (rule.min && value.length < rule.min) {
                    errors[field] = ['Too few items'];
                } else if (rule.max && value.length > rule.max) {
                    errors[field] = ['Too many items'];
                }
                break;

            default:
                throw new Error(`Unknown type: ${rule.type}`);
        }

        // Pattern check
        if (rule.pattern && typeof value === 'string' && !new RegExp(rule.pattern).test(value)) {
            errors[field] = ['Invalid format'];
            valid = false;
        }
    }

    return { valid, errors };
}