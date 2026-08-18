export function solve(input) {
    const schema = input.schema || {};
    const data = input.data || {};
    const errors = {};
    let isValid = true;

    // Iterate over fields present in the data to validate them against the schema
    for (const field in data) {
        if (!data.hasOwnProperty(field)) continue;

        const value = data[field];
        const rules = schema[field];

        // 1. Check existence and required status
        if (rules) {
            // Handle required check: If required, must not be null/undefined
            if (rules.required && (value === undefined || value === null)) {
                errors[field] = errors[field] ? [...errors[field], 'Required'] : ['Required'];
                isValid = false;
            }
        }

        // If the value is present and defined, proceed with type/constraint validation
        if (value !== undefined && value !== null) {
            const actualType = Array.isArray(value) ? 'array' : typeof value;
            const expectedType = rules ? rules.type : null;

            // 2. Type check
            if (expectedType && actualType !== expectedType) {
                errors[field] = errors[field] ? [...errors[field], 'Invalid type'] : ['Invalid type'];
                isValid = false;
            }

            // If types mismatch, stop further checks for this field to avoid confusing errors based on constraints.
            if (errors[field] && errors[field][0] === 'Invalid type') {
                continue;
            }


            // 3. Constraint checks (Only if type matches or is string/number/array)

            if (expectedType === 'string') {
                if (typeof value === 'string') {
                    const len = value.length;
                    if (rules.min !== undefined && len < rules.min) {
                        errors[field] = errors[field] ? [...errors[field], 'Too short'] : ['Too short'];
                    }
                    if (rules.max !== undefined && len > rules.max) {
                        errors[field] = errors[field] ? [...errors[field], 'Too long'] : ['Too long'];
                    }
                    if (rules.pattern) {
                        try {
                            // Use RegExp constructor for validation
                            const regex = new RegExp(rules.pattern);
                            if (!regex.test(value)) {
                                errors[field] = errors[field] ? [...errors[field], 'Invalid format'] : ['Invalid format'];
                            }
                        } catch (e) {
                             // Handle invalid regex pattern if necessary, though prompt implies valid regex strings
                        }
                    }
                }

            } else if (expectedType === 'number') {
                if (typeof value === 'number') {
                    if (rules.min !== undefined && value < rules.min) {
                        errors[field] = errors[field] ? [...errors[field], 'Too small'] : ['Too small'];
                    }
                    if (rules.max !== undefined && value > rules.max) {
                        errors[field] = errors[field] ? [...errors[field], 'Too large'] : ['Too large'];
                    }
                }

            } else if (expectedType === 'array') {
                if (Array.isArray(value)) {
                    const len = value.length;
                    if (rules.min !== undefined && len < rules.min) {
                        errors[field] = errors[field] ? [...errors[field], 'Too few items'] : ['Too few items'];
                    }
                    if (rules.max !== undefined && len > rules.max) {
                        errors[field] = errors[field] ? [...errors[field], 'Too many items'] : ['Too many items'];
                    }
                }
            }
        }
    }

    // Final cleanup: remove any fields that were not present in the schema but might have generated spurious data checks (not strictly necessary based on prompt, but good practice)
    // We focus only on errors found.

    return {
        valid: isValid,
        errors: errors
    };
}