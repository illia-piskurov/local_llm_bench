export function solve(input) {
    const validate = (schema, data, path) => {
        if (!schema || !data) return { valid: false, errors: [] };

        if (Array.isArray(schema)) {
            return {
                valid: schema.every((item, index) =>
                    validate(item, data[index], `${path}/items/${index}`)
                ),
                errors: []
            };
        }

        const type = schema.type;

        switch (type) {
            case 'string':
                return {
                    valid: typeof data === 'string' && (schema.minLength ? data.length >= schema.minLength : true),
                    errors: []
                };

            case 'number':
                return {
                    valid: typeof data === 'number',
                    errors: []
                };

            case 'boolean':
                return {
                    valid: typeof data === 'boolean',
                    errors: []
                };

            case 'object':
                const required = schema.required || [];
                const additionalProperties = schema.additionalProperties !== false;

                if (!additionalProperties && !Object.keys(data).every(key => required.includes(key))) {
                    return {
                        valid: false,
                        errors: [{ path, message: "Required properties are missing" }]
                    };
                }

                let suberrors = [];

                for (const [key, subSchema] of Object.entries(schema.properties || {})) {
                    const subPath = `${path}/properties/${key}`;
                    const value = data[key];
                    const result = validate(subSchema, value, subPath);
                    if (!result.valid) suberrors.push(...result.errors);
                }

                return {
                    valid: suberrors.length === 0,
                    errors: [...suberrors]
                };

            case 'array':
                if (Array.isArray(schema.items)) {
                    return {
                        valid: data.every((item, index) =>
                            validate(schema.items[index], item, `${path}/items/${index}`)
                        ),
                        errors: []
                    };
                }

                const result = validate(schema.items || {}, data[0], path);
                return { ...result, valid: result.valid && data.length >= (schema.minItems || 0) };

            case 'enum':
                if (!Array.isArray(data)) {
                    return {
                        valid: false,
                        errors: [{ path, message: "Expected type array" }]
                    };
                }

                return {
                    valid: data.some(value => schema.enum.includes(value)),
                    errors: []
                };

            default:
                throw new Error(`Unsupported type: ${type}`);
        }
    };

    const definitions = input.definitions || {};
    const schemaPath = input.schema;
    const dataPath = input.data;

    let resolvedSchema = null;
    let resolvedData = null;

    if (schemaPath.startsWith("#/definitions")) {
        const parts = schemaPath.split("/").slice(2);
        resolvedSchema = definitions[parts.join("/")];
    }

    if (dataPath.startsWith("#/")) {
        const pathParts = dataPath.split("/");
        let current = input;
        for (const part of pathParts.slice(1)) {
            if (!current || typeof current !== 'object') return { valid: false, errors: [{ path: dataPath, message: "Invalid data structure" }] };
            current = current[part];
        }
        resolvedData = current;
    } else {
        throw new Error("Invalid input.data path");
    }

    if (!resolvedSchema || !resolvedData) return { valid: false, errors: [] };

    return validate(resolvedSchema, resolvedData, "#");
}