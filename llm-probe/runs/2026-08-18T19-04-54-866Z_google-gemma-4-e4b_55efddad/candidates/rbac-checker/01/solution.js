export function solve(input) {
    /**
     * Checks if a rule matches a requested permission, supporting *, prefix:* rules.
     * @param {string} rule - The rule defined in config (e.g., "posts:*", "*").
     * @param {string} permission - The actual requested permission (e.g., "posts:view").
     * @returns {boolean} True if matched, false otherwise.
     */
    const matchesRule = (rule, permission) => {
        if (!rule) return false;
        // Super wildcard
        if (rule === '*') {
            return true;
        }

        // Namespace wildcard (e.g., "posts:*")
        if (typeof rule === 'string' && rule.endsWith(':*') && rule.length > 1) {
            const prefix = rule.substring(0, rule.length - 2); // Removes ':*' -> e.g., "posts:"
            return permission.startsWith(prefix);
        }

        // Exact match
        return rule === permission;
    };

    const results = [];

    for (const request of input.requests) {
        const user = request.user;
        const requestedPermission = request.permission;
        let isGranted = false;

        // 1. Handle User Not Found (Rule 4)
        const userConfig = input.users[user];
        if (!userConfig) {
            results.push(false);
            continue;
        }

        // --- CHECK DENIALS (Rule 1) ---
        let isDenied = false;
        if (userConfig.denies && Array.isArray(userConfig.denies)) {
            for (const denyRule of userConfig.denies) {
                if (matchesRule(denyRule, requestedPermission)) {
                    isDenied = true;
                    break;
                }
            }
        }

        // If explicitly denied, access is false regardless of other rules.
        if (isDenied) {
            results.push(false);
            continue;
        }

        // --- CHECK GRANTS (Rule 3) ---
        
        // A. Check Explicit Allows
        if (userConfig.allows && Array.isArray(userConfig.allows)) {
            for (const allowRule of userConfig.allows) {
                if (matchesRule(allowRule, requestedPermission)) {
                    isGranted = true;
                    break; 
                }
            }
        }

        // B. Check Roles/Roles Grants
        if (!isGranted && userConfig.roles && Array.isArray(userConfig.roles)) {
            for (const roleName of userConfig.roles) {
                const rolePermissions = input.roles[roleName];
                if (rolePermissions && Array.isArray(rolePermissions)) {
                    for (const rule of rolePermissions) {
                        if (matchesRule(rule, requestedPermission)) {
                            isGranted = true;
                            break; // Found grant via roles
                        }
                    }
                }
                if (isGranted) {
                    break; // Stop checking other roles
                }
            }
        }

        results.push(isGranted);
    }

    return results;
}