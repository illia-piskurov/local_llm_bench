export function solve(input) {
    if (!input || !Array.isArray(input.nodes)) {
        return [];
    }

    const nodeMap = new Map();
    const roots = [];

    // Build a map of id to node
    input.nodes.forEach(node => {
        nodeMap.set(node.id, { ...node, children: [] });
    });

    // Group nodes by parent
    const parentChildrenMap = new Map();

    input.nodes.forEach(node => {
        const parentId = node.parentId;
        if (parentId === null || parentId === undefined) {
            roots.push(node.id);
        } else {
            if (!parentChildrenMap.has(parentId)) {
                parentChildrenMap.set(parentId, []);
            }
            parentChildrenMap.get(parentId).push(node.id);
        }
    });

    // Build the tree structure
    const result = [];

    roots.forEach(rootId => {
        const root = nodeMap.get(rootId);
        if (!root) return;

        // Get children from parentChildrenMap
        const childrenIds = parentChildrenMap.get(rootId) || [];
        const children = childrenIds.map(id => {
            const childNode = nodeMap.get(id);
            if (!childNode) return null;
            return {
                ...childNode,
                children: []
            };
        }).filter(Boolean);

        // Assign children to root
        root.children = children;

        // Recursively build children trees
        children.forEach(child => {
            const childChildrenIds = parentChildrenMap.get(child.id) || [];
            const childChildren = childChildrenIds.map(id => {
                const childNode = nodeMap.get(id);
                if (!childNode) return null;
                return {
                    ...childNode,
                    children: []
                };
            }).filter(Boolean);

            child.children = childChildren;
        });

        result.push(root);
    });

    return result;
}