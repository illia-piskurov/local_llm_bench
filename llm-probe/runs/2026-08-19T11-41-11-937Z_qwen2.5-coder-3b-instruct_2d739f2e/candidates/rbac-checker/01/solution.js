export function solve(input) {
  const roles = input.roles;
  const users = input.users;
  const requests = input.requests;

  return requests.map(request => {
    const user = request.user;
    const permission = request.permission;

    // Check if the user is found in the users object
    if (!users[user]) {
      return false;
    }

    const rolesForUser = users[user].roles || [];
    const allows = users[user].allows || [];
    const denies = users[user].denies || [];

    // Check if any rule in denies matches the requested permission
    for (const deny of denies) {
      if (matches(deny, permission)) {
        return false;
      }
    }

    // Check if any role grants the permission
    for (const role of rolesForUser) {
      if (matches(roles[role], permission)) {
        return true;
      }
    }

    // Check if the permission is listed in allows
    if (allows.includes(permission)) {
      return true;
    }

    // If none of the above conditions are met, access is denied
    return false;
  });
}

// Helper function to match a rule with a permission using wildcard support
function matches(rule, permission) {
  const regex = new RegExp(`^${rule}$`);
  return regex.test(permission);
}