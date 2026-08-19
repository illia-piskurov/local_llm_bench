export function solve(input) {
  const nodes = input.nodes;
  const idMap = new Map();
  
  // Copy each node and give it an empty children array
  for (const n of nodes) {
    const copy = { ...n, children: [] };
    idMap.set(copy.id, copy);
  }
  
  // Attach each node to its parent if exists (preserves order)
  for (const n of nodes) {
    if (n.parentId !== null && (idMap.get(n.parentId))) {
      const parent = idMap.get(n.parentId);
      parent.children.push(n);
    }
  }
  
  // Gather root nodes in original input order
  const roots = [];
  for (const n of nodes) {
    if (n.parentId === null || !idMap.has(n.parentId)) {
      roots.push(idMap.get(n.id));
    }
  }
  
  return roots;
}