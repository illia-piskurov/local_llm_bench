export function solve(input) {
    const idToNode = {};
    for (const node of input.nodes) {
      const newNode = { ...node, children: [] };
      idToNode[node.id] = newNode;
    }

    for (const node of input.nodes) {
      const parentId = node.parentId;
      if (parentId !== null && idToNode[parentId]) {
        idToNode[parentId].children.push({ ...node, children: [] });
      }
    }

    const roots = input.nodes.filter(node => {
      return node.parentId === null || !idToNode[node.parentId];
    });

    return roots;
}