export function solve(input) {
    const nodes = input.nodes || [];

    if (nodes.length === 0) {
        return [];
    }

    // Step 1: Index all nodes by ID and initialize children arrays
    const nodeMap = {};
    for (const node of nodes) {
        nodeMap[node.id] = {
            ...node,
            children: []
        };
    }

    // Step 2: Build the hierarchy (link parents and children)
    for (const node of nodes) {
        const nodeId = node.id;
        const parentId = node.parentId;

        if (parentId !== null && parentId !== undefined) {
            const parentNode = nodeMap[parentId];
            
            // If the parent exists, add the current node to its children list.
            // We check existence defensively, although problem constraints imply valid IDs usually exist if parentId is set.
            if (parentNode) {
                parentNode.children.push(nodeMap[nodeId]);
            }
        }
    }

    // Step 3: Identify root nodes
    const roots = [];
    
    // Iterate through the map keys to ensure we process nodes in their original input order
    for (const id in nodeMap) {
        const node = nodeMap[id];
        
        // A node is a root if its parentId is null or if the parentId doesn't exist in the set of nodes.
        if (node.parentId === null || !(node.parentId in nodeMap)) {
            roots.push(node);
        }
    }

    return roots;
}