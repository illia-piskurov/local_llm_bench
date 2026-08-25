export function solve(input) {
    const n = input.n;
    const edges = input.edges;

    if (n === 0) return [];

    // 1. Initialization: Build Adjacency List and In-Degree array
    // Use Arrays for fixed size structures like degrees, Maps/Objects for adjacency lists if nodes are sparse, but since n is small enough (and we index from 0 to n-1), arrays are fine here.
    const adj = Array(n).fill(0).map(() => []);
    const inDegree = Array(n).fill(0);

    for (const [u, v] of edges) {
        adj[u].push(v);
        inDegree[v]++;
    }

    // 2. Queue Setup: Find all nodes with in-degree 0
    const queue = [];
    for (let i = 0; i < n; i++) {
        if (inDegree[i] === 0) {
            queue.push(i);
        }
    }

    const result = [];
    let head = 0; // Pointer for queue simulation

    // 3. Processing (Kahn's Algorithm)
    while (head < queue.length) {
        const u = queue[head++];
        result.push(u);

        for (const v of adj[u]) {
            inDegree[v]--;
            if (inDegree[v] === 0) {
                queue.push(v);
            }
        }
    }

    // 4. Result Check
    if (result.length === n) {
        return result;
    } else {
        // Cycle detected
        return null;
    }
}