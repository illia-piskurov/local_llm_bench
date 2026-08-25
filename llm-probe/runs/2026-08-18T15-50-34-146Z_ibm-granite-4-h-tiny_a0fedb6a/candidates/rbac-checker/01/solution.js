export function solve(input) {
  const roles = input.roles;
  const users = input.users;

  return input.requests.map(request => {
    const userRoles = (users[request.user]?.roles || []).map(role => `${role}.*`);
    const allPermissionsToAllow = new Set([...userRoles, ...input.users[request.user]?.allows?.filter(p => p)?.map(p => p.split(':')[0] + ':*')]);

    for (const role of userRoles) {
      if (allPermissionsToAllow.has(`${roles[role].join('|')}.*`) || allPermissionsToAllow.has('*')) {
        return true;
      }
    }

    const deny = users[request.user]?.denies?.find(p => p === request.permission);
    if (deny !== undefined) {
      return false;
    }

    for (const role of userRoles) {
      if (roles[role].includes(request.permission)) {
        return true;
      }
    }

    if (allPermissionsToAllow.has(`${request.permission}.*`) || allPermissionsToAllow.has('*')) {
      return true;
    }

    return false;
  });
}