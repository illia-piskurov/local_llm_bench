export function solve(input) {
    const nodesMap = new Map();
    
    // Populate a map with node objects for quick lookup by id.
    input.nodes.forEach(node => {
        nodesMap.set(node.id, { ...node });
    });

    // Create the root nodes.
    const roots = [];
    input.nodes.forEach(node => {
        if (node.parentId === null) {
            roots.push(nodesMap.get(node.id));
        }
    });

    // Populate children for each node in the tree.
    roots.forEach(root => {
        root.children = input.nodes.filter(child => child.parentId === root.id)
                                  .map(child => nodesMap.get(child.id));
    });

    return roots;
}