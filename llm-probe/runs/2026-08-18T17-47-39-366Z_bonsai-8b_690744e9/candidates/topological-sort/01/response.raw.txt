export function solve(input) {
  const n = input.n;
  const edges = input.edges;

  // Build adjacency list and in-degree count
  const adj = new Array(n).fill().map(() => []);
  const inDegree = new Array(n).fill(0);

  for (const [from, to] of edges) {
    adj[from].push(to);
    inDegree[to]++;
  }

  // Initialize queue with nodes having in-degree 0
  const queue = [];
  for (let i = 0; i < n; i++) {
    if (inDegree[i] === 0) queue.push(i);
  }

  // Perform topological sort
  const result = [];

  while (queue.length > 0) {
    const node = queue.shift();
    result.push(node);

    for (const neighbor of adj[node]) {
      inDegree[neighbor]--;
      if (inDegree[neighbor] === 0) queue.push(neighbor);
    }
  }

  // If the result contains all nodes, it is a valid topological ordering
  if (result.length === n) return result;
  return null;
}