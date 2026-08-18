export function solve(input) {
  const nodes = input.nodes;
  const rootNodes = [];

  function buildTree(node, parentId) {
    if (node.parentId === null || node.parentId === undefined) {
      rootNodes.push({ ...node, children: [] });
      return;
    }
    const childNodes = nodes.filter(n => n.parentId === node.id);
    for (const child of childNodes) {
      buildTree(child, node.id);
    }
  }

  buildTree(nodes[0], null);

  // Preserve order and structure
  const result = rootNodes.map(node => ({
    ...node,
    children: node.children || []
  }));
  return result;
}