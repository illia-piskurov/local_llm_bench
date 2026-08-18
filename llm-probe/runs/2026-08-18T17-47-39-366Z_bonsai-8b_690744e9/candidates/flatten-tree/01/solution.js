export function solve(input) {
  if (!input.root || input.root === null) return [];

  const result = [];
  const queue = [[input.root, result]];

  while (queue.length > 0) {
    const [node, parentList] = queue.shift();
    if (!node.left && !node.right) continue;

    parentList.push(node.value);
    queue.push([node.left, parentList]);
    queue.push([node.right, parentList]);
  }

  return result;
}