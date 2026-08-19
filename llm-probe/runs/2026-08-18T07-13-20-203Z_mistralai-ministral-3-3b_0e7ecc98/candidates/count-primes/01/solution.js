export function solve(input) {
    const n = input.n;
    if (n <= 2) return 0;

    let count = 0;
    for (let num = 2; num < n; num++) {
        let isPrime = true;
        for (let i = 2, maxDivisor = Math.sqrt(num); i <= maxDivisor; i++) {
            if (num % i === 0) {
                isPrime = false;
                break;
            }
        }
        if (isPrime) count++;
    }
    return count;
}