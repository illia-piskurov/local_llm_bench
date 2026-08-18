export function solve(input) {
    if (!input || !input.nodes) {
        return [];
    }

    // Pass 1: Initialize copies and build a lookup map by ID.
    // We must use copies so we don't mutate the input structure, but links (references)
    // between parent/child objects in the map will correctly form the tree.
    const nodeMap = new Map();
    for (const originalNode of input.nodes) {
        // Initialize children array immediately for all nodes.
        const newNodeCopy = { ...originalNode, children: [] };
        nodeMap.set(originalNode.id, newNodeCopy);
    }

    // Pass 2: Build the hierarchy and identify roots while preserving order.
    const finalRoots = [];

    for (const originalNode of input.nodes) {
        // Get the mutable, copied object for this node.
        const currentNodeObj = nodeMap.get(originalNode.id);
        const parentId = originalNode.parentId;

        if (parentId === null || typeof parentId === undefined || !nodeMap.has(parentId)) {
            // This node is a root (either explicitly parentId: null, or its parent ID doesn't exist).
            finalRoots.push(currentNodeObj);
        } else {
            // Find the parent object in the map using the parent ID.
            const parentObj = nodeMap.get(parentId);

            // Append the current node to its parent's children array.
            if (parentObj) {
                // Because we iterate over input.nodes sequentially, appending here preserves 
                // the relative order of siblings correctly.
                parentObj.children.push(currentNodeObj);
            }
        }
    }

    return finalRoots;
}