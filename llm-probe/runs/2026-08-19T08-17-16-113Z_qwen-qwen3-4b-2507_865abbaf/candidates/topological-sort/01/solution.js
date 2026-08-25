export function solve(input) {
    const n = input.n;
    const edges = input.edges || [];
    
    // Build adjacency list and in-degree map
    const adj = Array(n).fill().map(() => []);
    const inDegree = Array(n).fill(0);
    
    for (const [from, to] of edges) {
        adj[from].push(to);
        inDegree[to]++;
    }
    
    // Find all nodes with in-degree 0
    const queue = [];
    for (let i = 0; i < n; i++) {
        if (inDegree[i] === 0) {
            queue.push(i);
        }
    }
    
    // Topological sort using Kahn's algorithm
    const result = [];
    
    while (queue.length > 0) {
        const node = queue.shift();
        result.push(node);
        
        // Update in-degrees of neighbors
        for (const neighbor of adj[node]) {
            inDegree[neighbor]--;
            if (inDegree[neighbor] === 0) {
                queue.push(neighbor);
            }
        }
    }
    
    // If result length is less than n, there's a cycle
    return result.length === n ? result : null;
}