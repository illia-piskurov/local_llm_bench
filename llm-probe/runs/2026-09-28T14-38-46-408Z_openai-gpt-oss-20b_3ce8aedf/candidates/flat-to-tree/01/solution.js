export function solve(input) {
  const nodes = Array.isArray(input.nodes) ? input.nodes : [];
  const map = new Map();
  for (const n of nodes) {
    map.set(n.id, { ...n, children: [] });
  }
  const roots = [];
  for (const n of nodes) {
    const nodeCopy = map.get(n.id);
    if (n.parentId == null || !map.has(n.parentId)) {
      roots.push(nodeCopy);
    } else {
      const parent = map.get(n.parentId);
      parent.children.push(nodeCopy);
    }
  }
  return roots;
}