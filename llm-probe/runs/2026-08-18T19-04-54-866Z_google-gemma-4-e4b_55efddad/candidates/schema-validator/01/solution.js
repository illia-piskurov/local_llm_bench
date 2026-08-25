export function solve(input) {
    const schema = input?.schema || {};
    const data = input?.data || {};
    const errors = {};

    // Helper to add an error for a field if it's not already present
    function addError(field, message) {
        if (!errors[field]) {
            errors[field] = [];
        }
        errors[field].push(message);
    }

    for (const field in schema) {
        if (!schema.hasOwnProperty(field)) continue;

        const rule = schema[field];
        let value = data[field];
        let currentFieldErrors = [];

        // --- 1. Required Check ---
        const isRequiredMissing = rule.required && (value === undefined || value === null);

        if (isRequiredMissing) {
            currentFieldErrors.push('Required');
        }

        // Determine if the subsequent type/constraint checks should run.
        // If it fails required and nothing was provided, we might stop here for simplicity, 
        // but since we must collect ALL errors, we proceed unless it's completely undefined AND not required.
        const isValuePresent = value !== undefined && value !== null;

        // --- 2. Type Check ---
        let typeMismatch = false;
        let expectedType = rule.type;

        if (expectedType) {
            switch (expectedType) {
                case 'string':
                    if (typeof value !== 'string') {
                        typeMismatch = true;
                    }
                    break;
                case 'number':
                    if (typeof value !== 'number' && !isNaN(value)) { // Allows NaN if provided, but standard JS validation usually treats numbers strictly. Let's stick to typeof number.
                         if (typeof value !== 'number') {
                             typeMismatch = true;
                         }
                    }
                    break;
                case 'boolean':
                    if (typeof value !== 'boolean') {
                        typeMismatch = true;
                    }
                    break;
                case 'array':
                    if (!Array.isArray(value)) {
                        typeMismatch = true;
                    }
                    break;
            }

            if (typeMismatch) {
                currentFieldErrors.push('Invalid type');
            }
        }
        
        // --- 3. Constraint Checks (Min/Max/Pattern) ---
        
        // Only run constraints if the value exists AND passed basic typing checks.
        // We skip constraint checks if 'Required' failed, as those errors cover emptiness sufficiently.
        const canRunConstraints = isValuePresent && !currentFieldErrors.includes('Invalid type');


        if (canRunConstraints) {
            switch (expectedType) {
                case 'string':
                    const strValue = String(value);
                    // Min/Max Length
                    if (rule.min !== undefined && strValue.length < rule.min) {
                        currentFieldErrors.push('Too short');
                    }
                    if (rule.max !== undefined && strValue.length > rule.max) {
                        currentFieldErrors.push('Too long');
                    }
                    // Pattern
                    if (rule.pattern) {
                        try {
                            const regex = new RegExp(rule.pattern);
                            if (!regex.test(strValue)) {
                                currentFieldErrors.push('Invalid format');
                            }
                        } catch (e) {
                             // Ignore malformed patterns in schema for robustness
                        }
                    }
                    break;

                case 'number':
                    const numValue = Number(value);
                    // Min/Max Value
                    if (rule.min !== undefined && numValue < rule.min) {
                        currentFieldErrors.push('Too small');
                    }
                    if (rule.max !== undefined && numValue > rule.max) {
                        currentFieldErrors.push('Too large');
                    }
                    break;

                case 'array':
                    const arrayLength = value ? value.length : 0;
                    // Min/Max Items
                    if (rule.min !== undefined && arrayLength < rule.min) {
                        currentFieldErrors.push('Too few items');
                    }
                    if (rule.max !== undefined && arrayLength > rule.max) {
                        currentFieldErrors.push('Too many items');
                    }
                    break;
            }
        }


        // Collect all field errors
        if (currentFieldErrors.length > 0) {
            errors[field] = currentFieldErrors;
        }
    }

    const valid = Object.keys(errors).length === 0;

    return {
        valid: valid,
        errors: errors
    };
}