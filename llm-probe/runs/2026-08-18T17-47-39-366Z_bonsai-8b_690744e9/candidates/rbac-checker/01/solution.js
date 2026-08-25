export function solve(input) {
  const results = [];

  for (const request of input.requests) {
    const user = request.user;
    const permission = request.permission;

    // Check if user exists in the input
    if (!input.users[user]) {
      results.push(false);
      continue;
    }

    const roles = input.users[user].roles || [];
    const allows = input.users[user].allows || [];
    const denies = input.users[user].denies || [];

    // Check for explicit deny
    if (containsDeny(permission, denies)) {
      results.push(false);
      continue;
    }

    // Check if permission is allowed by any role
    if (roles.some(role => containsPermission(permission, role))) {
      results.push(true);
      continue;
    }

    // Check if permission is in allows
    if (allows.includes(permission)) {
      results.push(true);
      continue;
    }

    // Default case: not granted
    results.push(false);
  }

  return results;
}

// Helper function to check if a permission matches a role
function containsPermission(permission, role) {
  const permissionParts = permission.split(':');
  const roleParts = role.split(':');

  // Namespace wildcard: '*' in the role parts (e.g., 'posts:*' matches any namespace)
  if (roleParts[1] === '*') {
    return true;
  }

  // Super wildcard: '*' in the permission parts (e.g., '*read*')
  if (permissionParts[1] === '*') {
    return true;
  }

  // Exact match
  return permissionParts.join(':') === roleParts.join(':');
}

// Helper function to check if a permission is denied by any rule
function containsDeny(permission, denies) {
  const denyParts = denies.split(':');
  const permParts = permission.split(':');

  // Namespace wildcard: '*' in the deny parts (e.g., 'articles:*' matches any article)
  if (denyParts[1] === '*') {
    return true;
  }

  // Super wildcard: '*' in the permission parts (e.g., '*delete*' matches any delete action)
  if (permParts[1] === '*') {
    return true;
  }

  // Exact match
  return denyParts.join(':') === permParts.join(':');
}