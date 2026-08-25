export function solve(root) {
  if (!root) {
    return [];
  }

  const result = [];
  const queue = [root];

  while (queue.length > 0) {
    // Dequeue the current node
    const node = queue[0];
    queue.shift();

    // Process the value
    result.push(node.value);

    // Enqueue children if they exist
    if (node.left) {
      queue.push(node.left);
    }
    if (node.right) {
      queue.push(node.right);
    }
  }

  return result;
}