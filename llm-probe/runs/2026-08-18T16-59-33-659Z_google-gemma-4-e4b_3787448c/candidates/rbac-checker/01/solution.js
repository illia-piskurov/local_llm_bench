export function solve(input) {

    /**
     * Checks if a single rule string matches the requested permission string.
     * Matches: exact match, namespace wildcard (e.g., 'posts:*'), or super wildcard ('*').
     * @param {string} requestedPermission The permission being checked.
     * @param {string} rule The rule granted/checked against.
     * @returns {boolean} True if the rule matches the request.
     */
    const matchesRule = (requestedPermission, rule) => {
        if (rule === '*') {
            return true; // Super wildcard always matches
        }
        if (rule === requestedPermission) {
            return true; // Exact match
        }
        // Check for namespace wildcard pattern (e.g., 'posts:*')
        if (rule.endsWith(':*')) {
            const prefix = rule.substring(0, rule.length - 2);
            // Does the requested permission start with this prefix and contain a colon?
            // We assume structured permissions like 'scope:action'
            return requestedPermission.startsWith(prefix + ':');
        }
        return false;
    };

    /**
     * Determines if a user has access to a specific requested permission.
     * @param {{user: string, permission: string}} request The request details.
     * @param {object} input The full system input object.
     * @returns {boolean} True if access is granted and not denied.
     */
    const checkAccess = (request, input) => {
        const userId = request.user;
        const requestedPermission = request.permission;
        const user = input.users ? input.users[userId] : undefined;

        // Rule 4: If user not found, result is false.
        if (!user) {
            return false;
        }

        // Rule 1: Explicit denies override everything.
        if (user.denies && Array.isArray(user.denies)) {
            for (const denyRule of user.denies) {
                if (matchesRule(requestedPermission, denyRule)) {
                    return false;
                }
            }
        }

        // Rule 3: Access is granted if any role grants it OR if listed in user's 'allows'.
        let isGranted = false;

        // Check roles
        if (input.roles && Array.isArray(user.roles)) {
            for (const roleName of user.roles) {
                const rules = input.roles[roleName];
                if (rules && Array.isArray(rules)) {
                    for (const rule of rules) {
                        if (matchesRule(requestedPermission, rule)) {
                            isGranted = true;
                            break; // Found grant via role, stop checking roles
                        }
                    }
                }
                if (isGranted) break;
            }
        }

        // Check user allows list (Only if not already granted by role check)
        if (!isGranted && user.allows && Array.isArray(user.allows)) {
            for (const allowedRule of user.allows) {
                if (matchesRule(requestedPermission, allowedRule)) {
                    isGranted = true;
                    break;
                }
            }
        }

        return isGranted;
    };


    const results = input.requests.map(request => checkAccess(request, input));
    return results;
}