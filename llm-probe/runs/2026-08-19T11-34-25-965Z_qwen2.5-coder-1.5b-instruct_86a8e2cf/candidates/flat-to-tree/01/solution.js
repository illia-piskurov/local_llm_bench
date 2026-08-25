export function solve(input) {
  const nodes = input.nodes;
  const treeNodes = nodes.reduce((acc, node) => {
    if (!node.parentId) acc.push(node);
    else {
      const parent = nodes.find(n => n.id === node.parentId);
      if (parent) {
        parent.children ||= [];
        parent.children.push(node);
      }
    }
    return acc;
  }, []);

  // Preserve original relative order for roots
  treeNodes.sort((a, b) => a.id - b.id);

  return treeNodes;
}