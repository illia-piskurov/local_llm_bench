export function solve(input) {
  const nodesById = new Map();
  for (const node of input.nodes) {
    nodesById.set(node.id, node);
  }

  const roots = [];
  for (const node of input.nodes) {
    if (node.parentId === null || !nodesById.has(node.parentId)) {
      let children = [];
      for (const childNode of input.nodes) {
        if (childNode.parentId === node.id) {
          children.push(childNode);
        }
      }
      node.children = children;
      roots.push({ ...node });
    }
  }

  return roots;
}