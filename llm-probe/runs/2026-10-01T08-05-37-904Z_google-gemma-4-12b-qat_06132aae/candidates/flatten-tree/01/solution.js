export function solve(input) {
  const root = input && input.root;
  if (!root) {
    return [];
  }

  const result = [];
  const queue = [root];
  let head = 0;

  while (head < queue.length) {
    const node = queue[head++];
    result.push(node.value);

    if (node.left !== null && node.left !== undefined) {
      queue.push(node.left);
    }
    if (node.right !== null && node.right !== undefined) {
      queue.push(node.right);
    }
  }

  return result;
}