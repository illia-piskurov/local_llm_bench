export function solve(input) {
  const nodes = input.nodes || [];
  const nodeMap = new Map();
  const roots = [];

  // First pass: create cloned objects with a children array and store them in a map
  // This ensures we do not mutate the original input nodes.
  nodes.forEach(node => {
    nodeMap.set(node.id, { ...node, children: [] });
  });

  // Second pass: build the tree structure
  // By iterating through the original nodes array, we maintain the relative order
  // for both the roots and the children of each parent.
  nodes.forEach(node => {
    const newNode = nodeMap.get(node.id);
    const parentId = node.parentId;

    // A node is a root if its parentId is null, undefined, 
    // or if the parentId does not exist in the input nodes.
    if (parentId === null || parentId === undefined || !nodeMap.has(parentId)) {
      roots.push(newNode);
    } else {
      const parentNode = nodeMap.get(parentId);
      parentNode.children.push(newNode);
    }
  });

  return roots;
}