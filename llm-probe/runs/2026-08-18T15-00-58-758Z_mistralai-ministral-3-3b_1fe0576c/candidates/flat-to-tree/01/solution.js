export function solve(input) {
    const nodes = input.nodes;
    const nodeMap = new Map();
    const roots = [];

    // Build a map of nodes by id for quick lookup
    nodes.forEach(node => {
        nodeMap.set(node.id, { ...node });
    });

    // Identify root nodes (parentId is null or not in the map)
    nodes.forEach(node => {
        if (!node.parentId || !nodeMap.has(node.parentId)) {
            roots.push({ ...node });
        }
    });

    // Build children relationships
    const result = [];
    for (const root of roots) {
        const children = [];
        const parentNode = nodeMap.get(root.id);

        nodes.forEach(node => {
            if (node.parentId === parentNode.id && !children.some(child => child.id === node.id)) {
                children.push({ ...node });
            }
        });

        result.push({
            ...root,
            children: children.length > 0 ? children : []
        });
    }

    return result;
}