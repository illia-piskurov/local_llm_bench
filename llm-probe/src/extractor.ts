export function extractCode(response: string): string | undefined {
  const fenced = /```(?:javascript|js)?\s*\r?\n([\s\S]*?)```/i.exec(response);
  const candidate = (fenced?.[1] ?? response).trim();
  return candidate.includes("export function solve") ? candidate : undefined;
}
