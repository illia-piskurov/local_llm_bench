export function solve(input) {
  const n = input.n;
  const edges = input.edges;

  // Build adjacency list and indegree counts
  const adj = Array.from({ length: n }, () => []);
  const indeg = new Int32Array(n);

  for (const [u, v] of edges) {
    adj[u].push(v);
    indeg[v]++;
  }

  // Queue of nodes with zero indegree
  const queue = [];
  for (let i = 0; i < n; i++) if (indeg[i] === 0) queue.push(i);

  const result = [];
  let qIndex = 0;
  while (qIndex < queue.length) {
    const u = queue[qIndex++];
    result.push(u);
    for (const v of adj[u]) {
      indeg[v]--;
      if (indeg[v] === 0) queue.push(v);
    }
  }

  return result.length === n ? result : null;
}