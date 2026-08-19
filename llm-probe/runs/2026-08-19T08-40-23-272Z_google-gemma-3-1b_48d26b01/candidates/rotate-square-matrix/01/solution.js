export function solve(input) {
  const [[a,b],[c,d]] = input;
  const rotatedMatrix = [[d,c], [a, b]];
  return rotatedMatrix;
}