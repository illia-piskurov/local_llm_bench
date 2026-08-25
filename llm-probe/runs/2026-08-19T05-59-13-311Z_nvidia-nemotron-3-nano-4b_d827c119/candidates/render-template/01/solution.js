export function solve(input) {
    const template = input.template;
    return template.replace(/{{([^}]+)}}/g, (_, raw) => {
        let s = raw.trim();
        if (!s) return '';
        try {
            const parts = s.split('.');
            let value = input.data;
            for (const part of parts) {
                if (value === null || typeof value !== 'object') return '';
                // array index
                const idx = Number(part);
                if (Array.isArray(value)) {
                    if (!Number.isFinite(idx) || idx < 0 || idx >= value.length) return '';
                    value = value[idx];
                    continue;
                }
                // regular property lookup
                value = value[part] ?? {};
                if (value === undefined) return '';
            }
            const res = String(value);
            return res;
        } catch {
            return '';
        }
    });
}