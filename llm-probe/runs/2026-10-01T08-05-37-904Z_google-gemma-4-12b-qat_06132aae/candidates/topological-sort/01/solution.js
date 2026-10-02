export function solve(input) {
  const { n, edges } = input;
  const adj = Array.from({ length: n }, () => []);
  const inDegree = new Array(n).fill(0);

  for (let i = 0; i < edges.length; i++) {
    const [u, v] = edges[i];
    adj[u].push(v);
    inDegree[v]++;
  }

  const queue = [];
  for (let i = 0; i < n; i++) {
    if (inDegree[i] === 0) {
      queue.push(i);
    }
  }

  const result = [];
  let head = 0;
  while (head < queue.length) {
    const u = queue[head++];
    result.push(u);

    const neighbors = adj[u];
    for (let i = 0; i < neighbors.length; i++) {
      const v = neighbors[i];
      inDegree[v]--;
      if (inDegree[v] === 0) {
        queue.push(v);
      }
    }
  }

  return result.length === n ? result : null;
}