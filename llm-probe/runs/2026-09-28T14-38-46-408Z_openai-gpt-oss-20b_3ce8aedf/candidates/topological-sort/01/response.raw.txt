export function solve(input) {
  const n = input.n;
  const edges = input.edges;

  // Build adjacency list and indegree counts without mutating input
  const adj = Array.from({ length: n }, () => []);
  const indegree = new Uint32Array(n);

  for (const [from, to] of edges) {
    adj[from].push(to);
    indegree[to]++;
  }

  // Initialize queue with nodes of indegree 0
  const queue = [];
  for (let i = 0; i < n; i++) {
    if (indegree[i] === 0) queue.push(i);
  }

  const order = [];
  let head = 0;
  while (head < queue.length) {
    const v = queue[head++];
    order.push(v);
    for (const w of adj[v]) {
      indegree[w]--;
      if (indegree[w] === 0) queue.push(w);
    }
  }

  // If all nodes processed, return order; otherwise cycle detected
  return order.length === n ? order : null;
}