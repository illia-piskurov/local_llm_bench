export function solve(input) {
  const result = [];
  if (!input || !input.root) return result;
  const queue = [input.root];
  while (queue.length) {
    const node = queue.shift();
    if (!node) continue;
    result.push(node.value);
    if (node.left) queue.push(node.left);
    if (node.right) queue.push(node.right);
  }
  return result;
}