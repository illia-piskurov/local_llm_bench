export function solve(input) {
    const { n, edges } = input;
    const adj = Array.from({ length: n }, () => []);
    const inDegree = new Array(n).fill(0);

    for (const [from, to] of edges) {
        adj[from].push(to);
        inDegree[to]++;
    }

    const queue = [];
    for (let i = 0; i < n; i++) {
        if (inDegree[i] === 0) queue.push(i);
    }

    let result = [];
    while (queue.length > 0) {
        const u = queue.shift();
        result.push(u);

        for (const v of adj[u]) {
            inDegree[v]--;
            if (inDegree[v] === 0) queue.push(v);
        }
    }

    return inDegree.some(d => d !== 0) ? null : result;
}