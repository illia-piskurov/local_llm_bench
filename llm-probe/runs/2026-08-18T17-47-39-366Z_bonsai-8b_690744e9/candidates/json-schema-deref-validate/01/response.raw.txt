export function solve(input) {
  const { valid, errors } = input;
  const schema = input.schema;

  if (!schema || !schema.type) return { valid: false, errors };

  const definitionRef = schema.$ref;
  if (definitionRef && definitionRef.includes("#/definitions")) {
    const definitions = input.definitions;
    const refPath = definitionRef.replace("#/definitions/", "#");
    const key = refPath.split("/")?.pop() || "default";
    if (!definitions[key]) return { valid: false, errors };
    schema = definitions[key];
  }

  if (schema.type === "object") {
    if (schema.required) {
      for (const key of schema.required) {
        if (!(key in input)) return { valid: false, errors };
      }
    } else if (schema.additionalProperties) {
      for (const key in input) {
        if (key !== "properties" && !schema.properties[key]) {
          return { valid: false, errors };
        }
      }
    } else if (!schema.properties) {
      return { valid: false, errors };
    }

    const properties = schema.properties;
    for (const prop in input) {
      if (prop === "properties") continue;

      const propSchema = properties[prop];
      if (!propSchema || !propSchema.type) {
        return { valid: false, errors };
      }

      const value = input[prop];
      if (propSchema.type === "string" && propSchema.minLength) {
        if (value.length < propSchema.minLength) {
          return { valid: false, errors };
        }
      } else if (propSchema.type === "number") {
        if (typeof value !== "number" || isNaN(value)) {
          return { valid: false, errors };
        }
      } else if (propSchema.type === "boolean") {
        if (!(value instanceof Boolean)) {
          return { valid: false, errors };
        }
      } else if (propSchema.type === "array") {
        const items = propSchema.items;
        if (!items || !Array.isArray(items)) {
          return { valid: false, errors };
        }

        const length = propSchema.minItems || 0;
        if (length < 1) length = 1;

        for (let i = 0; i < length; i++) {
          const item = input[prop][i];
          if (!item || !Array.isArray(item)) {
            return { valid: false, errors };
          }

          const itemSchema = items[i];
          if (!itemSchema || !itemSchema.type) {
            return { valid: false, errors };
          }

          const val = item;
          if (itemSchema.type === "string" && itemSchema.enum) {
            if (!itemSchema.enum.includes(val)) {
              return { valid: false, errors };
            }
          } else if (itemSchema.type !== "number") {
            if (typeof val !== "number" || isNaN(val)) {
              return { valid: false, errors };
            }
          }
        }
      } else if (propSchema.type === "object") {
        const item = input[prop];
        if (!item || !Array.isArray(item)) {
          return { valid: false, errors };
        }

        const itemsSchema = propSchema.items;
        if (!itemsSchema) {
          return { valid: false, errors };
        }

        const length = propSchema.minItems || 0;
        if (length < 1) length = 1;

        for (let i = 0; i < length; i++) {
          const itemVal = itemsSchema[i];
          const val = item[i];

          if (!itemVal || !Array.isArray(itemVal)) {
            return { valid: false, errors };
          }

          const itemSchema = itemVal;
          if (!itemSchema || !itemSchema.type) {
            return { valid: false, errors };
          }

          const valType = itemSchema.type;
          if (valType === "string" && itemSchema.enum) {
            if (!itemSchema.enum.includes(val)) {
              return { valid: false, errors };
            }
          } else if (valType !== "number") {
            if (typeof val !== "number" || isNaN(val)) {
              return { valid: false, errors };
            }
          }
        }
      }
    }

    return { valid: true, errors };
  } else if (schema.type === "string" && schema.minLength) {
    const value = input;
    if (typeof value !== "string" || value.length < schema.minLength) {
      return { valid: false, errors };
    }
    return { valid: true, errors };
  } else if (schema.type === "number" && schema.minValue && schema.maxValue) {
    const value = input;
    if (typeof value !== "number" || value < schema.minValue || value > schema.maxValue) {
      return { valid: false, errors };
    }
    return { valid: true, errors };
  } else if (schema.type === "boolean") {
    const value = input;
    if (!(value instanceof Boolean)) {
      return { valid: false, errors };
    }
    return { valid: true, errors };
  } else if (schema.type === "array" && schema.items) {
    const items = schema.items;
    if (!Array.isArray(items)) {
      return { valid: false, errors };
    }

    const length = schema.minItems || 0;
    if (length < 1) length = 1;

    for (let i = 0; i < length; i++) {
      const itemSchema = items[i];
      if (!itemSchema || !Array.isArray(itemSchema)) {
        return { valid: false, errors };
      }

      const val = input[i];
      if (typeof val !== "object" || Array.isArray(val) && val.length === 0) {
        return { valid: false, errors };
      }

      const itemType = itemSchema.type;
      if (itemType === "string" && itemSchema.enum) {
        if (!itemSchema.enum.includes(val)) {
          return { valid: false, errors };
        }
      } else if (itemType !== "number") {
        if (typeof val !== "number" || isNaN(val)) {
          return { valid: false, errors };
        }
      }

      const itemResult = solve({ data: val });
      if (!itemResult.valid) {
        return { valid: false, errors };
      }
    }
    return { valid: true, errors };
  } else {
    return { valid: false, errors };
  }
}