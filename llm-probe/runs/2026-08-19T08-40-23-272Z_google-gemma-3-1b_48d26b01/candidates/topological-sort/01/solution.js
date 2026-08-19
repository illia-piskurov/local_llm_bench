export function solve(input) {
  const n = input.n;
  const edges = input.edges;

  const graph = new Array(n).fill(null);

  for (const edge of edges) {
    graph[edge[0]] = edge[1];
    graph[edge[1]] = edge[0];
  }

  const inDegree = new Array(n).fill(0);
  for (let i = 0; i < n; i++) {
    for (const edge of edges) {
      if (edge[0] === i || edge[1] === i) {
        inDegree[i]++;
      }
    }
  }

  const queue = [];
  for (let i = 0; i < n; i++) {
    if (inDegree[i] === 0) {
      queue.push(i);
    }
  }

  const result = [];
  while (queue.length > 0) {
    let node = queue.shift();
    result.push(node);

    for (let i = 0; i < n; i++) {
      if (graph[i] === node) {
        inDegree[i]--;
        if (inDegree[i] === 0) {
          queue.push(i);
        }
      }
    }
  }

  return result.length > 0 ? result : null;
}