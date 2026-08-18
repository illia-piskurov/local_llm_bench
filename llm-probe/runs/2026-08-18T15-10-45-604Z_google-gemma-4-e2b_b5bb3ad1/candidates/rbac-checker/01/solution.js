export function solve(input) {
    const roles = input.roles || {};
    const users = input.users || {};
    const requests = input.requests || [];
    const results = [];

    /**
     * Checks if a requested permission matches a granted rule, considering wildcards.
     * Rule 2: exact match, namespace wildcard (e.g., 'posts:*'), or super wildcard ('*').
     * @param {string} requestedPerm - The permission being checked (e.g., 'posts:read')
     * @param {string} grantedRule - A rule from a role or allows list (e.g., 'posts:*' or 'articles:read')
     * @returns {boolean} True if they match according to the rules.
     */
    function matches(requestedPerm, grantedRule) {
        if (grantedRule === '*') {
            return true;
        }
        if (requestedPerm === grantedRule) {
            return true;
        }
        // Namespace wildcard check: e.g., 'posts:*' matches 'posts:read'
        if (grantedRule.startsWith(requestedPerm) && grantedRule.length > requestedPerm && grantedRule[requestedPerm.length] === ':') {
            return true;
        }
        return false;
    }

    for (const request of requests) {
        const { user, permission } = request;
        let accessGranted = false;

        // Rule 4: If user not found, result is false.
        const userData = users[user];
        if (!userData) {
            results.push(false);
            continue;
        }

        // Rule 1: Explicit denies override everything.
        if (userData.denies && userData.denies.includes(permission)) {
            results.push(false);
            continue;
        }

        // Check Role Grants (Rule 3 part 1)
        if (userData.roles) {
            for (const role of userData.roles) {
                if (roles[role]) {
                    const grantedPermissions = roles[role];
                    for (const grantedPerm of grantedPermissions) {
                        if (matches(permission, grantedPerm)) {
                            accessGranted = true;
                            break; // Found a granting role/permission
                        }
                    }
                }
                if (accessGranted) break;
            }
        }

        // Check Explicit Allows (Rule 3 part 2) - Only checked if not already granted via roles
        if (!accessGranted && userData.allows) {
            if (userData.allows.includes(permission)) {
                accessGranted = true;
            }
        }

        results.push(accessGranted);
    }

    return results;
}