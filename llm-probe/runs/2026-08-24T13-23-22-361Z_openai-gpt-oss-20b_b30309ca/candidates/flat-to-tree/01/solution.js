export function solve(input) {
  const nodes = input.nodes || [];
  const nodeMap = new Map();

  // Create copies with children arrays
  for (const n of nodes) {
    nodeMap.set(n.id, { ...n, children: [] });
  }

  const roots = [];

  // Build tree preserving order
  for (const n of nodes) {
    const copy = nodeMap.get(n.id);
    if (n.parentId == null || !nodeMap.has(n.parentId)) {
      roots.push(copy);
    } else {
      const parent = nodeMap.get(n.parentId);
      parent.children.push(copy);
    }
  }

  return roots;
}