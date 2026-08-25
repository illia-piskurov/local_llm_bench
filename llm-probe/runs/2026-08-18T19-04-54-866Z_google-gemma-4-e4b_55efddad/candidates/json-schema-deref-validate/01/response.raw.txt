export function solve(input) {
    const definitions = input.definitions || {};
    let errors = [];

    /**
     * Resolves a JSON Pointer reference ($ref) against the provided definitions object.
     * The expected format is relative to definitions: #/definitions/<Name> or deeper paths.
     * @param {string} refString - The $ref string (e.g., "#/definitions/User").
     * @returns {object|null} The resolved schema definition, or null if not found.
     */
    function resolveRef(refString) {
        if (!refString || typeof refString !== 'string') return null;

        // Strip the leading hash and slashes: #/definitions/User -> definitions/User
        const path = refString.substring(1);

        let currentContext = definitions;
        let parts = path.split("/");

        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];

            if (!part) continue;

            // Handle the initial segment, which must be within definitions
            if (parts[0] === 'definitions') {
                currentContext = definitions;
                continue;
            }

            try {
                // If we are already inside a definition object path
                if (typeof currentContext !== 'object' || currentContext === null) return null;

                const nextNode = currentContext[part];
                if (nextNode && typeof nextNode === 'object') {
                    currentContext = nextNode;
                } else {
                    return null; // Path segment not found or invalid structure
                }
            } catch (e) {
                return null;
            }
        }
        // If the traversal ended successfully, currentContext is the resolved schema.
        return currentContext;
    }

    /**
     * Checks if a given data value matches the expected JSON type keywords.
     * @param {*} data - The value to check.
     * @param {string|Array<string>} types - Expected type string(s).
     * @returns {boolean} True if type matches, false otherwise.
     */
    function checkTypeMatch(data, types) {
        if (typeof types === 'string') {
            types = [types];
        }

        const dataType = typeof data;
        if (types.includes('object') && data !== null) {
            // JSON Schema treats objects and arrays specially
            if (Array.isArray(data)) return types.includes('array');
            return true; // Must be an object if not array/null, unless 'null' was allowed by schema keywords not covered here
        }

        for (const expectedType of types) {
            if (expectedType === 'string' && typeof data === 'string') return true;
            if (expectedType === 'number' && (typeof data === 'number' && !isNaN(data))) return true;
            if (expectedType === 'boolean' && typeof data === 'boolean') return true;
            if (expectedType === 'array' && Array.isArray(data)) return true;
            if (expectedType === 'object' && typeof data === 'object' && data !== null) {
                // This catches plain objects, excluding arrays which were caught above
                return !Array.isArray(data);
            }
        }
        return false;
    }


    /**
     * Recursively validates data against a schema structure.
     * @param {*} data - The data value.
     * @param {object} schema - The current JSON Schema object.
     * @param {string} pathPrefix - The full JSON Pointer path to the current location (e.g., "#/items/0").
     */
    function validate(data, schema, pathPrefix) {
        // 1. Handle $ref resolution
        let currentSchema = schema;
        if (schema.$ref) {
            const resolved = resolveRef(schema.$ref);
            if (!resolved) {
                errors.push({ path: pathPrefix, message: `Reference failed to resolve for ${schema.$ref}` });
                return; // Cannot validate if reference fails
            }
            currentSchema = resolved;
        }

        // 2. Primary type validation check (handles keywords like 'type')
        const schemaType = currentSchema.type;

        if (schemaType) {
            const allowedTypes = Array.isArray(schemaType) ? schemaType : [schemaType];
            if (!checkTypeMatch(data, allowedTypes)) {
                errors.push({ path: pathPrefix, message: `Expected type ${allowedTypes.join(' or ')}` });
                // If type validation fails here, we often stop deeper structural checks for this node.
                return;
            }
        }

        const schemaProperties = currentSchema;

        if (schemaProperties.enum) {
            if (!Array.isArray(data) || !schemaProperties.enum.includes(data)) {
                errors.push({ path: pathPrefix, message: `Value not in enum [${schemaProperties.enum.join(', ')}]` });
            }
        }

        // --- Structural Validation based on Type ---
        if (Array.isArray(data) && schemaProperties.type === 'array') {
            const itemsSchema = schemaProperties.items;
            if (!itemsSchema) return; // No item validation needed if missing

            if (schemaProperties.minItems !== undefined && data.length < schemaProperties.minItems) {
                errors.push({ path: pathPrefix, message: `Minimum array length is ${schemaProperties.minItems}` });
            }

            // Validate items element by element
            for (let i = 0; i < data.length; i++) {
                const itemPath = `${pathPrefix}/items/${i}`;
                validate(data[i], itemsSchema, itemPath);
            }
        } else if (!Array.isArray(data) && typeof data === 'object' && schemaProperties.type === 'object') {
            const properties = currentSchema.properties || {};

            // A. Check required fields presence
            if (currentSchema.required && Array.isArray(currentSchema.required)) {
                for (const key of currentSchema.required) {
                    if (!(key in data)) {
                        errors.push({ path: `${pathPrefix}/${key}`, message: `Required property missing` });
                    }
                }
            }

            // B. Validate defined properties
            for (const propKey in properties) {
                if (!properties.hasOwnProperty(propKey)) continue;

                const propSchema = properties[propKey];
                const propPath = `${pathPrefix}/${propKey}`;
                
                // Only validate if the key exists in data OR if required check passed AND we proceed regardless.
                if (Object.prototype.hasOwnProperty.call(data, propKey)) {
                    validate(data[propKey], propSchema, propPath);
                } else if (!currentSchema.required || !currentSchema.required.includes(propKey) && propschema.$ref) {
                     // Skip validation of missing optional properties unless they are required
                }
            }

            // C. Check additional properties (disallowing unlisted keys)
            if (currentSchema.additionalProperties === false) {
                for (const key in data) {
                    if (!properties[key]) {
                        errors.push({ path: `${pathPrefix}/${key}`, message: "Additional properties are not allowed" });
                    }
                }
            }
        } else if (typeof data === 'string' && schemaProperties.type === 'string') {
            if (schemaProperties.minLength !== undefined) {
                const min = parseInt(schemaProperties.minLength);
                if (data.length < min) {
                    errors.push({ path: pathPrefix, message: `Minimum length is ${min}` });
                }
            }
        }

    }

    // Start validation from the root context
    validate(input.data, input.schema, "#");


    return {
        valid: errors.length === 0,
        errors: errors
    };
}