export function solve(input) {
  const nodes = Object.entries(input.nodes).map(([_, node]) => ({ ...node, id: Number(node.id), name: node.name, parentId: Number(node.parentId) }));

  const nodeMap = new Map();
  for (const node of nodes) {
    nodeMap.set(Number(node.id), node);
  }

  const rootNodes = [];
  for (const [id, node] of entries(nodeMap)) {
    if (node && node.getParentId() === null) {
      rootNodes.push({ ...node, children: [] });
    }
  }

  nodes.forEach((node) => {
    if (node.parentId !== null) {
      const parent = nodeMap.get(Number(node.parentId));
      if (parent) {
        parent.children.push({ ...node, parentId: node.getParentId() });
      }
    }
  });

  return rootNodes;
}