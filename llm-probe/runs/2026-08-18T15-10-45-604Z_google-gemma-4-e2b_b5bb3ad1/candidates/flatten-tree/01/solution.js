export function solve(input) {
    if (!input || !input.root) {
        return [];
    }

    const root = input.root;
    
    // Handle case where the actual tree root object might be null, though input structure implies it exists.
    if (!root) {
        return [];
    }

    // Initialize queue for BFS and result array
    const queue = [root];
    const result = [];

    while (queue.length > 0) {
        // Dequeue the current node
        const currentNode = queue.shift();

        // Add its value to the result
        result.push(currentNode.value);

        // Enqueue children if they exist
        const left = currentNode.left;
        if (left) {
            queue.push(left);
        }

        const right = currentNode.right;
        if (right) {
            queue.push(right);
        }
    }

    return result;
}