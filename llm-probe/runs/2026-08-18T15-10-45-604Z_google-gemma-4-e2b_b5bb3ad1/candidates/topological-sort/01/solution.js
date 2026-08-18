export function solve(input) {
    const n = input.n;
    const edges = input.edges;

    if (n === 0) {
        return [];
    }

    // 1. Initialize Adjacency List and In-degree array
    const adj = Array(n).fill(0).map(() => []);
    const inDegree = Array(n).fill(0);

    // 2. Build graph and calculate in-degrees
    for (const [u, v] of edges) {
        // Assuming 0 <= u, v < n based on problem context
        adj[u].push(v);
        inDegree[v]++;
    }

    // 3. Initialize queue for Kahn's algorithm
    const queue = [];
    for (let i = 0; i < n; i++) {
        if (inDegree[i] === 0) {
            queue.push(i);
        }
    }

    // 4. Perform Topological Sort
    const result = [];
    let head = 0; // Using index for queue simulation for slight optimization over shift() if implemented carefully, but standard push/shift is clearer here. We stick to standard array manipulation.

    while (queue.length > 0) {
        // Dequeue a node u
        const u = queue.shift();
        result.push(u);

        // Iterate through neighbors v
        for (const v of adj[u]) {
            inDegree[v]--;
            if (inDegree[v] === 0) {
                queue.push(v);
            }
        }
    }

    // 5. Check for cycle
    if (result.length === n) {
        return result;
    } else {
        // A cycle exists if we couldn't process all nodes
        return null;
    }
}