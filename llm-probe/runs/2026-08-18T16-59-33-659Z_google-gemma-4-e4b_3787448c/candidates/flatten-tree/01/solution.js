export function solve(input) {
    const root = input && input.root;

    if (!root) {
        return [];
    }

    // Queue for BFS traversal. We use a JS array simulating the queue.
    let queue = [];
    queue.push(root);

    const result = [];

    while (queue.length > 0) {
        // Dequeue operation: Get and remove the element at the front of the queue
        const currentNode = queue.shift();

        // Process the current node's value
        result.push(currentNode.value);

        // Enqueue left child if it exists
        if (currentNode.left) {
            queue.push(currentNode.left);
        }

        // Enqueue right child if it exists
        if (currentNode.right) {
            queue.push(currentNode.right);
        }
    }

    return result;
}