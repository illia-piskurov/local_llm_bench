import type { Task } from "./types.js";

const task = (definition: Task): Task => definition;

export const coreTasks: ReadonlyArray<Task> = [
  // ── PRODUCT (Real-world data & business logic) ────────────────────────────
  task({
    id: "flat-to-tree",
    category: "product",
    title: "Convert flat array to tree",
    prompt: "Convert a flat array of nodes in input.nodes (each node has id: string|number, name: string, and parentId: string|number|null) into a hierarchical tree where each node has a children array containing its direct child nodes. Roots have parentId: null or parentId not present in input.nodes. Return an array of root nodes in their original relative order. Each node's children array must also preserve original relative order. Every node in the output must include a children array (empty array [] if no children).",
    examples: [
      {
        id: "example",
        input: {
          nodes: [
            { id: 1, name: "Root", parentId: null },
            { id: 2, name: "Child A", parentId: 1 },
            { id: 3, name: "Child B", parentId: 1 }
          ]
        },
        expected: [
          {
            id: 1,
            name: "Root",
            parentId: null,
            children: [
              { id: 2, name: "Child A", parentId: 1, children: [] },
              { id: 3, name: "Child B", parentId: 1, children: [] }
            ]
          }
        ]
      }
    ],
    tests: [
      { id: "empty", input: { nodes: [] }, expected: [] },
      {
        id: "multiple-roots",
        input: {
          nodes: [
            { id: "r1", name: "Root 1", parentId: null },
            { id: "r2", name: "Root 2", parentId: null },
            { id: "c1", name: "Child 1", parentId: "r1" }
          ]
        },
        expected: [
          {
            id: "r1",
            name: "Root 1",
            parentId: null,
            children: [{ id: "c1", name: "Child 1", parentId: "r1", children: [] }]
          },
          { id: "r2", name: "Root 2", parentId: null, children: [] }
        ]
      },
      {
        id: "orphan-as-root",
        input: {
          nodes: [
            { id: 10, name: "Orphan", parentId: 999 },
            { id: 11, name: "Child of Orphan", parentId: 10 }
          ]
        },
        expected: [
          {
            id: 10,
            name: "Orphan",
            parentId: 999,
            children: [{ id: 11, name: "Child of Orphan", parentId: 10, children: [] }]
          }
        ]
      },
      {
        id: "deep-nesting",
        input: {
          nodes: [
            { id: 1, name: "L1", parentId: null },
            { id: 2, name: "L2", parentId: 1 },
            { id: 3, name: "L3", parentId: 2 },
            { id: 4, name: "L4", parentId: 3 }
          ]
        },
        expected: [
          {
            id: 1,
            name: "L1",
            parentId: null,
            children: [
              {
                id: 2,
                name: "L2",
                parentId: 1,
                children: [
                  {
                    id: 3,
                    name: "L3",
                    parentId: 2,
                    children: [{ id: 4, name: "L4", parentId: 3, children: [] }]
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    referenceCode: `export function solve(input) {
  const nodes = input.nodes || [];
  if (nodes.length === 0) return [];
  const map = new Map();
  for (const n of nodes) {
    map.set(n.id, { ...n, children: [] });
  }
  const roots = [];
  for (const n of nodes) {
    const current = map.get(n.id);
    if (n.parentId !== null && map.has(n.parentId)) {
      map.get(n.parentId).children.push(current);
    } else {
      roots.push(current);
    }
  }
  return roots;
}`,
    mutants: [
      // drops orphans instead of treating them as roots
      `export function solve(input) {
  const nodes = input.nodes || [];
  if (nodes.length === 0) return [];
  const map = new Map();
  for (const n of nodes) {
    map.set(n.id, { ...n, children: [] });
  }
  const roots = [];
  for (const n of nodes) {
    const current = map.get(n.id);
    if (n.parentId === null) {
      roots.push(current);
    } else if (map.has(n.parentId)) {
      map.get(n.parentId).children.push(current);
    }
  }
  return roots;
}`
    ]
  }),

  task({
    id: "paginate-and-sort",
    category: "product",
    title: "Filter, sort and paginate list",
    prompt: "Process an array of records in input.items with filtering, sorting, and pagination:\n1. Filter: if input.filter is provided ({ field: string, op: 'eq'|'neq'|'gt'|'gte'|'lt'|'lte'|'contains', value: any }), filter items. For 'contains', perform case-insensitive substring matching on String(item[field]).\n2. Sort: if input.sort is provided ({ field: string, dir: 'asc'|'desc' }), sort items. Stable sort preserving original relative order for ties.\n3. Paginate: input.page (1-indexed, default 1), input.pageSize (default 10). Return { items: any[], total: number, page: number, totalPages: number }. If total is 0, totalPages must be 0.",
    examples: [
      {
        id: "example",
        input: {
          items: [
            { id: 1, name: "Apples", qty: 10 },
            { id: 2, name: "Bananas", qty: 5 },
            { id: 3, name: "Avocados", qty: 8 }
          ],
          filter: { field: "name", op: "contains", value: "a" },
          sort: { field: "qty", dir: "asc" },
          page: 1,
          pageSize: 2
        },
        expected: {
          items: [
            { id: 2, name: "Bananas", qty: 5 },
            { id: 3, name: "Avocados", qty: 8 }
          ],
          total: 3,
          page: 1,
          totalPages: 2
        }
      }
    ],
    tests: [
      {
        id: "empty",
        input: { items: [] },
        expected: { items: [], total: 0, page: 1, totalPages: 0 }
      },
      {
        id: "numeric-gt-filter",
        input: {
          items: [{ val: 10 }, { val: 20 }, { val: 30 }, { val: 40 }],
          filter: { field: "val", op: "gt", value: 20 },
          page: 1,
          pageSize: 10
        },
        expected: {
          items: [{ val: 30 }, { val: 40 }],
          total: 2,
          page: 1,
          totalPages: 1
        }
      },
      {
        id: "desc-sort-and-second-page",
        input: {
          items: [{ id: "a", p: 100 }, { id: "b", p: 300 }, { id: "c", p: 200 }],
          sort: { field: "p", dir: "desc" },
          page: 2,
          pageSize: 2
        },
        expected: {
          items: [{ id: "a", p: 100 }],
          total: 3,
          page: 2,
          totalPages: 2
        }
      },
      {
        id: "contains-case-insensitive",
        input: {
          items: [{ tag: "TypeScript" }, { tag: "python" }, { tag: "JavaScript" }],
          filter: { field: "tag", op: "contains", value: "SCRIPT" }
        },
        expected: {
          items: [{ tag: "TypeScript" }, { tag: "JavaScript" }],
          total: 2,
          page: 1,
          totalPages: 1
        }
      }
    ],
    referenceCode: `export function solve(input) {
  let list = [...(input.items || [])];
  if (input.filter) {
    const { field, op, value } = input.filter;
    list = list.filter((item) => {
      const v = item[field];
      if (op === "eq") return v === value;
      if (op === "neq") return v !== value;
      if (op === "gt") return v > value;
      if (op === "gte") return v >= value;
      if (op === "lt") return v < value;
      if (op === "lte") return v <= value;
      if (op === "contains") {
        return String(v ?? "").toLowerCase().includes(String(value ?? "").toLowerCase());
      }
      return true;
    });
  }
  if (input.sort) {
    const { field, dir } = input.sort;
    const factor = dir === "desc" ? -1 : 1;
    list.sort((a, b) => {
      const va = a[field], vb = b[field];
      if (va < vb) return -1 * factor;
      if (va > vb) return 1 * factor;
      return 0;
    });
  }
  const total = list.length;
  const page = input.page ?? 1;
  const pageSize = input.pageSize ?? 10;
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const items = list.slice(start, start + pageSize);
  return { items, total, page, totalPages };
}`,
    mutants: [
      // case-sensitive contains
      `export function solve(input) {
  let list = [...(input.items || [])];
  if (input.filter) {
    const { field, op, value } = input.filter;
    list = list.filter((item) => {
      const v = item[field];
      if (op === "contains") return String(v ?? "").includes(String(value ?? ""));
      if (op === "gt") return v > value;
      return true;
    });
  }
  const total = list.length;
  const page = input.page ?? 1;
  const pageSize = input.pageSize ?? 10;
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const items = list.slice(start, start + pageSize);
  return { items, total, page, totalPages };
}`
    ]
  }),

  task({
    id: "deep-merge",
    category: "product",
    title: "Deep merge configurations",
    prompt: "Recursively merge an array of objects from input.objects from left to right (later objects override earlier ones). Rules: Plain objects are merged recursively by key. Arrays and primitive values are replaced entirely by the later value. Keys with undefined value are ignored (previous value is retained). Return a new plain object without mutating inputs. If input.objects is empty, return {}.",
    examples: [
      {
        id: "example",
        input: {
          objects: [
            { theme: { colors: { primary: "blue", secondary: "gray" } }, tags: [1, 2] },
            { theme: { colors: { primary: "red" } }, tags: [3] }
          ]
        },
        expected: {
          theme: { colors: { primary: "red", secondary: "gray" } },
          tags: [3]
        }
      }
    ],
    tests: [
      { id: "empty", input: { objects: [] }, expected: {} },
      {
        id: "array-replacement",
        input: {
          objects: [{ arr: [1, 2, 3] }, { arr: [4, 5] }]
        },
        expected: { arr: [4, 5] }
      },
      {
        id: "nested-three-layers",
        input: {
          objects: [
            { a: { b: { c: 1, d: 2 } } },
            { a: { b: { c: 99 } } },
            { a: { b: { e: 100 } } }
          ]
        },
        expected: { a: { b: { c: 99, d: 2, e: 100 } } }
      },
      {
        id: "primitive-overwrites-object",
        input: {
          objects: [{ val: { nested: true } }, { val: "plain_string" }]
        },
        expected: { val: "plain_string" }
      }
    ],
    referenceCode: `export function solve(input) {
  function isPlainObject(v) {
    return typeof v === "object" && v !== null && !Array.isArray(v);
  }
  function mergeTwo(target, source) {
    if (!isPlainObject(target) || !isPlainObject(source)) {
      return source === undefined ? target : source;
    }
    const out = { ...target };
    for (const key of Object.keys(source)) {
      const sv = source[key];
      if (sv === undefined) continue;
      if (isPlainObject(sv) && isPlainObject(out[key])) {
        out[key] = mergeTwo(out[key], sv);
      } else {
        out[key] = sv;
      }
    }
    return out;
  }
  const objects = input.objects || [];
  return objects.reduce((acc, curr) => mergeTwo(acc, curr), {});
}`,
    mutants: [
      // concatenates arrays instead of replacing
      `export function solve(input) {
  function isPlainObject(v) {
    return typeof v === "object" && v !== null && !Array.isArray(v);
  }
  function mergeTwo(target, source) {
    if (Array.isArray(target) && Array.isArray(source)) {
      return [...target, ...source];
    }
    if (!isPlainObject(target) || !isPlainObject(source)) {
      return source === undefined ? target : source;
    }
    const out = { ...target };
    for (const key of Object.keys(source)) {
      out[key] = mergeTwo(out[key], source[key]);
    }
    return out;
  }
  const objects = input.objects || [];
  return objects.reduce((acc, curr) => mergeTwo(acc, curr), {});
}`
    ]
  }),

  task({
    id: "csv-parse",
    category: "product",
    title: "Parse CSV text to objects",
    prompt: "Parse a CSV string in input.csv into an array of objects where keys are header column names from the first row. Rules:\n- Rows are separated by newline (\n or \r\n). Ignore empty lines at the end.\n- Values enclosed in double quotes \"...\" may contain commas and newlines; two double quotes \"\" represent an escaped quote.\n- Unquoted values should have leading/trailing whitespace trimmed. Quoted values preserve internal whitespace.\n- If input is empty or only has a header row, return [].",
    examples: [
      {
        id: "example",
        input: {
          csv: "name,age,city\nAlice,30,New York\n\"Smith, Bob\",25,\"Los \"\"Angeles\"\"\""
        },
        expected: [
          { name: "Alice", age: "30", city: "New York" },
          { name: "Smith, Bob", age: "25", city: "Los \"Angeles\"" }
        ]
      }
    ],
    tests: [
      { id: "empty", input: { csv: "" }, expected: [] },
      { id: "header-only", input: { csv: "col1,col2,col3" }, expected: [] },
      {
        id: "quoted-commas",
        input: {
          csv: "id,title\n1,\"Item, special edition\"\n2,Standard"
        },
        expected: [
          { id: "1", title: "Item, special edition" },
          { id: "2", title: "Standard" }
        ]
      },
      {
        id: "escaped-quotes-and-crlf",
        input: {
          csv: "code,desc\r\nA,\"He said \"\"Hello\"\"\"\r\nB,Simple\r\n"
        },
        expected: [
          { code: "A", desc: "He said \"Hello\"" },
          { code: "B", desc: "Simple" }
        ]
      }
    ],
    referenceCode: `export function solve(input) {
  const text = input.csv ?? "";
  if (!text.trim()) return [];
  const rows = [];
  let currentRow = [];
  let currentVal = "";
  let inQuotes = false;
  let i = 0;
  while (i < text.length) {
    const char = text[i];
    if (inQuotes) {
      if (char === '"') {
        if (i + 1 < text.length && text[i + 1] === '"') {
          currentVal += '"';
          i += 2;
          continue;
        } else {
          inQuotes = false;
          i++;
          continue;
        }
      } else {
        currentVal += char;
        i++;
        continue;
      }
    } else {
      if (char === '"') {
        inQuotes = true;
        i++;
        continue;
      } else if (char === ',') {
        currentRow.push(currentVal.trim());
        currentVal = "";
        i++;
        continue;
      } else if (char === '\\r') {
        if (i + 1 < text.length && text[i + 1] === '\\n') i++;
        currentRow.push(currentVal.trim());
        rows.push(currentRow);
        currentRow = [];
        currentVal = "";
        i++;
        continue;
      } else if (char === '\\n') {
        currentRow.push(currentVal.trim());
        rows.push(currentRow);
        currentRow = [];
        currentVal = "";
        i++;
        continue;
      } else {
        currentVal += char;
        i++;
        continue;
      }
    }
  }
  if (currentVal || currentRow.length > 0) {
    currentRow.push(currentVal.trim());
    rows.push(currentRow);
  }
  const validRows = rows.filter((r) => r.length > 1 || (r.length === 1 && r[0] !== ""));
  if (validRows.length <= 1) return [];
  const headers = validRows[0];
  const results = [];
  for (let r = 1; r < validRows.length; r++) {
    const obj = {};
    for (let c = 0; c < headers.length; c++) {
      obj[headers[c]] = validRows[r][c] ?? "";
    }
    results.push(obj);
  }
  return results;
}`,
    mutants: [
      // naive split by comma — fails on quoted commas
      `export function solve(input) {
  const lines = (input.csv || "").trim().split(/\\r?\\n/).filter(Boolean);
  if (lines.length <= 1) return [];
  const headers = lines[0].split(",").map(h => h.trim());
  return lines.slice(1).map(line => {
    const parts = line.split(",").map(p => p.trim());
    const obj = {};
    headers.forEach((h, i) => { obj[h] = parts[i] ?? ""; });
    return obj;
  });
}`
    ]
  }),

  task({
    id: "render-template",
    category: "product",
    title: "Render template string with variables",
    prompt: "Render a template string input.template by substituting {{path}} placeholders with values from input.data. Rules:\n- Placeholders support dot-notation path accessors (e.g. {{user.profile.name}} or {{items.0}}).\n- Whitespace inside braces must be trimmed: {{  key  }} is valid.\n- If a path resolves to undefined or null, or if intermediate path does not exist, substitute an empty string \"\".\n- Convert non-string primitive values (numbers, booleans) to string.\n- Return the resulting string.",
    examples: [
      {
        id: "example",
        input: {
          template: "Hello {{ user.name }}, you have {{ stats.unread }} messages! Active: {{ active }}",
          data: {
            user: { name: "Alice" },
            stats: { unread: 5 },
            active: true
          }
        },
        expected: "Hello Alice, you have 5 messages! Active: true"
      }
    ],
    tests: [
      {
        id: "nested-and-arrays",
        input: {
          template: "First: {{items.0.title}}, Second: {{items.1.title}}",
          data: { items: [{ title: "Apple" }, { title: "Banana" }] }
        },
        expected: "First: Apple, Second: Banana"
      },
      {
        id: "missing-and-whitespace",
        input: {
          template: "Name: [{{   user.name   }}], Missing: [{{ user.age }}], Nullable: [{{ extra }}]",
          data: { user: { name: "Bob" }, extra: null }
        },
        expected: "Name: [Bob], Missing: [], Nullable: []"
      },
      {
        id: "no-placeholders",
        input: { template: "Plain static text", data: { a: 1 } },
        expected: "Plain static text"
      },
      {
        id: "empty-template",
        input: { template: "", data: {} },
        expected: ""
      }
    ],
    referenceCode: `export function solve(input) {
  const { template, data } = input;
  if (!template) return "";
  return template.replace(/\\{\\{\\s*([^\\}]+?)\\s*\\}\\}/g, (_, path) => {
    const parts = path.trim().split(".");
    let cur = data;
    for (const part of parts) {
      if (cur === null || cur === undefined) return "";
      cur = cur[part];
    }
    if (cur === null || cur === undefined) return "";
    return String(cur);
  });
}`,
    mutants: [
      // only supports top level keys, no dot notation
      `export function solve(input) {
  const { template, data } = input;
  if (!template) return "";
  return template.replace(/\\{\\{\\s*([^\\}]+?)\\s*\\}\\}/g, (_, path) => {
    const val = (data || {})[path.trim()];
    return val === null || val === undefined ? "" : String(val);
  });
}`
    ]
  }),

  task({
    id: "shopping-cart",
    category: "product",
    title: "Calculate shopping cart totals",
    prompt: "Calculate totals for a shopping cart from input.items (array of { price: number, qty: number, category?: string }) and optional input.coupon and input.taxRate (e.g. 0.08 for 8%).\nRules:\n1. subtotal: sum of (price * qty) for all items.\n2. discount: from input.coupon (if provided):\n   - { type: 'percent', value: 20 }: 20% off subtotal.\n   - { type: 'fixed', value: 15 }: flat $15 off subtotal (capped at subtotal).\n   - { type: 'category_percent', category: 'food', value: 10 }: 10% off only items in that category.\n   If coupon is absent or unknown type, discount is 0. Discount cannot exceed subtotal.\n3. tax: Math.round((subtotal - discount) * taxRate * 100) / 100. (0 if taxRate omitted).\n4. total: Math.round((subtotal - discount + tax) * 100) / 100.\nRound subtotal, discount, tax, total to 2 decimal places (Math.round(x * 100) / 100). Return { subtotal, discount, tax, total }.",
    examples: [
      {
        id: "example",
        input: {
          items: [
            { price: 100, qty: 2, category: "electronics" },
            { price: 20, qty: 1, category: "books" }
          ],
          coupon: { type: "percent", value: 10 },
          taxRate: 0.05
        },
        expected: {
          subtotal: 220,
          discount: 22,
          tax: 9.9,
          total: 207.9
        }
      }
    ],
    tests: [
      {
        id: "empty",
        input: { items: [] },
        expected: { subtotal: 0, discount: 0, tax: 0, total: 0 }
      },
      {
        id: "category-discount",
        input: {
          items: [
            { price: 50, qty: 2, category: "clothing" },
            { price: 30, qty: 1, category: "food" }
          ],
          coupon: { type: "category_percent", category: "clothing", value: 20 },
          taxRate: 0.1
        },
        expected: {
          subtotal: 130,
          discount: 20,
          tax: 11,
          total: 121
        }
      },
      {
        id: "fixed-discount-capped",
        input: {
          items: [{ price: 10, qty: 1 }],
          coupon: { type: "fixed", value: 50 }
        },
        expected: {
          subtotal: 10,
          discount: 10,
          tax: 0,
          total: 0
        }
      },
      {
        id: "no-coupon-with-tax",
        input: {
          items: [{ price: 19.99, qty: 3 }],
          taxRate: 0.08
        },
        expected: {
          subtotal: 59.97,
          discount: 0,
          tax: 4.8,
          total: 64.77
        }
      }
    ],
    referenceCode: `export function solve(input) {
  const round = (v) => Math.round(v * 100) / 100;
  const items = input.items || [];
  let subtotal = 0;
  for (const item of items) {
    subtotal += (item.price || 0) * (item.qty || 0);
  }
  subtotal = round(subtotal);

  let discount = 0;
  const coupon = input.coupon;
  if (coupon && typeof coupon === "object") {
    if (coupon.type === "percent") {
      discount = subtotal * ((coupon.value || 0) / 100);
    } else if (coupon.type === "fixed") {
      discount = coupon.value || 0;
    } else if (coupon.type === "category_percent") {
      let catSum = 0;
      for (const item of items) {
        if (item.category === coupon.category) {
          catSum += (item.price || 0) * (item.qty || 0);
        }
      }
      discount = catSum * ((coupon.value || 0) / 100);
    }
  }
  discount = Math.min(subtotal, Math.max(0, discount));
  discount = round(discount);

  const taxRate = input.taxRate || 0;
  const taxableAmount = Math.max(0, subtotal - discount);
  const tax = round(taxableAmount * taxRate);
  const total = round(taxableAmount + tax);

  return { subtotal, discount, tax, total };
}`,
    mutants: [
      // calculates tax on subtotal before subtracting discount
      `export function solve(input) {
  const round = (v) => Math.round(v * 100) / 100;
  const items = input.items || [];
  let subtotal = round(items.reduce((acc, it) => acc + it.price * it.qty, 0));
  let discount = 0;
  if (input.coupon?.type === "category_percent") {
    discount = items.filter(it => it.category === input.coupon.category).reduce((acc, it) => acc + it.price * it.qty, 0) * (input.coupon.value / 100);
  }
  discount = round(discount);
  const tax = round(subtotal * (input.taxRate || 0));
  const total = round(subtotal - discount + tax);
  return { subtotal, discount, tax, total };
}`
    ]
  }),

  task({
    id: "query-string-parser",
    category: "product",
    title: "Parse URL query string to nested object",
    prompt: "Parse a URL query string from input.query (e.g. 'a=1&b[]=x&b[]=y&user[name]=Alice&user[age]=30') into a plain object.\nRules:\n- Strip leading '?' if present. If query is empty, return {}.\n- Pairs are separated by '&'. Keys and values are separated by '='. Decode keys and values using decodeURIComponent. If '=' is omitted, the value is boolean true.\n- Keys ending with '[]' (e.g. tags[]=js&tags[]=ts) collect values into an Array.\n- Keys with nested brackets (e.g. user[address][city]=Paris) create nested plain objects.\n- If a decoded value represents a finite number ('42', '-3.14'), parse it as number. If 'true' or 'false', parse as boolean. Otherwise keep as string.\n- Return the resulting plain object.",
    examples: [
      {
        id: "example",
        input: { query: "?search=laptop&filters[brand]=Apple&tags[]=sale&tags[]=m3&page=1&active=true" },
        expected: {
          search: "laptop",
          filters: { brand: "Apple" },
          tags: ["sale", "m3"],
          page: 1,
          active: true
        }
      }
    ],
    tests: [
      { id: "empty", input: { query: "" }, expected: {} },
      {
        id: "primitives-and-leading-qmark",
        input: { query: "?num=100&neg=-5&flag=false&str=hello" },
        expected: { num: 100, neg: -5, flag: false, str: "hello" }
      },
      {
        id: "array-brackets",
        input: { query: "items[]=a&items[]=b" },
        expected: { items: ["a", "b"] }
      },
      {
        id: "nested-object",
        input: { query: "user[address][city]=Paris&user[address][zip]=75001" },
        expected: { user: { address: { city: "Paris", zip: 75001 } } }
      },
      {
        id: "encoded-and-no-value-flag",
        input: { query: "name=John%20Doe&verified" },
        expected: { name: "John Doe", verified: true }
      }
    ],
    referenceCode: `export function solve(input) {
  let q = input.query || "";
  if (q.startsWith("?")) q = q.slice(1);
  if (!q.trim()) return {};

  function parseVal(v) {
    if (v === "true") return true;
    if (v === "false") return false;
    if (v !== "" && !isNaN(Number(v))) return Number(v);
    return v;
  }

  const result = {};
  const pairs = q.split("&").filter(Boolean);

  for (const pair of pairs) {
    const idx = pair.indexOf("=");
    let rawKey = idx === -1 ? pair : pair.slice(0, idx);
    let rawVal = idx === -1 ? undefined : pair.slice(idx + 1);

    const key = decodeURIComponent(rawKey);
    const val = rawVal === undefined ? true : parseVal(decodeURIComponent(rawVal));

    if (key.endsWith("[]")) {
      const baseKey = key.slice(0, -2);
      if (!Array.isArray(result[baseKey])) result[baseKey] = [];
      result[baseKey].push(val);
    } else if (key.includes("[") && key.endsWith("]")) {
      const parts = key.split(/[\\[\\]]/).filter(Boolean);
      let cur = result;
      for (let i = 0; i < parts.length - 1; i++) {
        const p = parts[i];
        if (!cur[p] || typeof cur[p] !== "object") cur[p] = {};
        cur = cur[p];
      }
      cur[parts[parts.length - 1]] = val;
    } else {
      result[key] = val;
    }
  }
  return result;
}`,
    mutants: [
      // leaves numbers and booleans as strings
      `export function solve(input) {
  let q = input.query || "";
  if (q.startsWith("?")) q = q.slice(1);
  if (!q.trim()) return {};
  const result = {};
  for (const pair of q.split("&").filter(Boolean)) {
    const [k, v] = pair.split("=");
    result[decodeURIComponent(k)] = v === undefined ? true : decodeURIComponent(v);
  }
  return result;
}`
    ]
  }),

  task({
    id: "schema-validator",
    category: "product",
    title: "Validate data against schema",
    prompt: "Validate an object input.data against input.schema.\nSchema is an object where keys map to rules:\n- type: 'string' | 'number' | 'boolean' | 'array'\n- required (boolean): if true and value is undefined or null, error is 'Required'\n- min (number): for string (min length -> 'Too short'), number (min value -> 'Too small'), array (min items -> 'Too few items')\n- max (number): for string (max length -> 'Too long'), number (max value -> 'Too large'), array (max items -> 'Too many items')\n- pattern (string): regex string for string values -> 'Invalid format'\nIf value is present and type does not match, error is 'Invalid type'.\nCollect all matching errors per field. Return { valid: boolean, errors: { [field]: string[] } }. If no errors, errors must be {} and valid must be true.",
    examples: [
      {
        id: "example",
        input: {
          schema: {
            username: { type: "string", required: true, min: 3 },
            age: { type: "number", min: 18 }
          },
          data: { username: "al", age: 16 }
        },
        expected: {
          valid: false,
          errors: {
            username: ["Too short"],
            age: ["Too small"]
          }
        }
      }
    ],
    tests: [
      {
        id: "all-valid",
        input: {
          schema: {
            email: { type: "string", required: true, pattern: "^\\S+@\\S+\\.\\S+$" },
            tags: { type: "array", min: 1 }
          },
          data: { email: "user@test.com", tags: ["a"] }
        },
        expected: { valid: true, errors: {} }
      },
      {
        id: "required-missing",
        input: {
          schema: { name: { type: "string", required: true } },
          data: { name: null }
        },
        expected: { valid: false, errors: { name: ["Required"] } }
      },
      {
        id: "type-mismatch",
        input: {
          schema: { count: { type: "number" } },
          data: { count: "not_a_number" }
        },
        expected: { valid: false, errors: { count: ["Invalid type"] } }
      },
      {
        id: "array-rules",
        input: {
          schema: { list: { type: "array", min: 2, max: 3 } },
          data: { list: [1] }
        },
        expected: { valid: false, errors: { list: ["Too few items"] } }
      }
    ],
    referenceCode: `export function solve(input) {
  const { schema = {}, data = {} } = input;
  const errors = {};

  function addErr(f, msg) {
    if (!errors[f]) errors[f] = [];
    errors[f].push(msg);
  }

  for (const [field, rule] of Object.entries(schema)) {
    const val = data[field];
    if (val === undefined || val === null) {
      if (rule.required) addErr(field, "Required");
      continue;
    }

    let typeMatches = false;
    if (rule.type === "array") {
      typeMatches = Array.isArray(val);
    } else if (rule.type === "string") {
      typeMatches = typeof val === "string";
    } else if (rule.type === "number") {
      typeMatches = typeof val === "number" && !isNaN(val);
    } else if (rule.type === "boolean") {
      typeMatches = typeof val === "boolean";
    }

    if (!typeMatches) {
      addErr(field, "Invalid type");
      continue;
    }

    if (rule.type === "string") {
      if (rule.min !== undefined && val.length < rule.min) addErr(field, "Too short");
      if (rule.max !== undefined && val.length > rule.max) addErr(field, "Too long");
      if (rule.pattern !== undefined && !new RegExp(rule.pattern).test(val)) addErr(field, "Invalid format");
    } else if (rule.type === "number") {
      if (rule.min !== undefined && val < rule.min) addErr(field, "Too small");
      if (rule.max !== undefined && val > rule.max) addErr(field, "Too large");
    } else if (rule.type === "array") {
      if (rule.min !== undefined && val.length < rule.min) addErr(field, "Too few items");
      if (rule.max !== undefined && val.length > rule.max) addErr(field, "Too many items");
    }
  }

  const valid = Object.keys(errors).length === 0;
  return { valid, errors };
}`,
    mutants: [
      // always marks valid as true
      `export function solve(input) {
  return { valid: true, errors: {} };
}`
    ]
  }),

  task({
    id: "state-reducer",
    category: "product",
    title: "Immutable state reducer",
    prompt: "Apply a list of actions in input.actions to initial state in input.state without mutating input.\nActions:\n- { type: 'SET', path: string, value: any }: sets property at dot-separated path (creates nested objects if missing).\n- { type: 'TOGGLE', path: string }: negates boolean at path (if value is not boolean, sets true).\n- { type: 'ARRAY_PUSH', path: string, item: any }: appends item to array at path (creates [item] if array missing).\n- { type: 'ARRAY_REMOVE', path: string, index: number }: removes element at index if within bounds.\n- { type: 'DELETE', path: string }: deletes key at path.\nReturn the resulting state object.",
    examples: [
      {
        id: "example",
        input: {
          state: { user: { name: "Bob", active: false }, tags: ["a", "b"] },
          actions: [
            { type: "TOGGLE", path: "user.active" },
            { type: "ARRAY_PUSH", path: "tags", item: "c" },
            { type: "ARRAY_REMOVE", path: "tags", index: 0 }
          ]
        },
        expected: {
          user: { name: "Bob", active: true },
          tags: ["b", "c"]
        }
      }
    ],
    tests: [
      {
        id: "nested-set-and-create-parents",
        input: {
          state: {},
          actions: [{ type: "SET", path: "config.theme.dark", value: true }]
        },
        expected: { config: { theme: { dark: true } } }
      },
      {
        id: "toggle-non-boolean",
        input: {
          state: { ready: "yes" },
          actions: [{ type: "TOGGLE", path: "ready" }]
        },
        expected: { ready: true }
      },
      {
        id: "delete-property",
        input: {
          state: { user: { name: "Alice", tempToken: "123" } },
          actions: [{ type: "DELETE", path: "user.tempToken" }]
        },
        expected: { user: { name: "Alice" } }
      },
      {
        id: "empty-actions",
        input: { state: { unchanged: 42 }, actions: [] },
        expected: { unchanged: 42 }
      }
    ],
    referenceCode: `export function solve(input) {
  let current = JSON.parse(JSON.stringify(input.state || {}));

  function getParts(p) {
    return p.split(".").filter(Boolean);
  }

  function applyAction(state, action) {
    const parts = getParts(action.path || "");
    if (parts.length === 0) return state;

    if (action.type === "SET") {
      let cur = state;
      for (let i = 0; i < parts.length - 1; i++) {
        const k = parts[i];
        if (!cur[k] || typeof cur[k] !== "object") cur[k] = {};
        cur = cur[k];
      }
      cur[parts[parts.length - 1]] = action.value;
    } else if (action.type === "TOGGLE") {
      let cur = state;
      for (let i = 0; i < parts.length - 1; i++) {
        const k = parts[i];
        if (!cur[k] || typeof cur[k] !== "object") cur[k] = {};
        cur = cur[k];
      }
      const last = parts[parts.length - 1];
      cur[last] = typeof cur[last] === "boolean" ? !cur[last] : true;
    } else if (action.type === "ARRAY_PUSH") {
      let cur = state;
      for (let i = 0; i < parts.length - 1; i++) {
        const k = parts[i];
        if (!cur[k] || typeof cur[k] !== "object") cur[k] = {};
        cur = cur[k];
      }
      const last = parts[parts.length - 1];
      if (!Array.isArray(cur[last])) cur[last] = [];
      cur[last].push(action.item);
    } else if (action.type === "ARRAY_REMOVE") {
      let cur = state;
      for (let i = 0; i < parts.length - 1; i++) {
        cur = cur?.[parts[i]];
      }
      const last = parts[parts.length - 1];
      if (cur && Array.isArray(cur[last])) {
        const idx = action.index;
        if (idx >= 0 && idx < cur[last].length) {
          cur[last].splice(idx, 1);
        }
      }
    } else if (action.type === "DELETE") {
      let cur = state;
      for (let i = 0; i < parts.length - 1; i++) {
        cur = cur?.[parts[i]];
      }
      if (cur && typeof cur === "object") {
        delete cur[parts[parts.length - 1]];
      }
    }
    return state;
  }

  const actions = input.actions || [];
  for (const act of actions) {
    applyAction(current, act);
  }
  return current;
}`,
    mutants: [
      // TOGGLE always sets false
      `export function solve(input) {
  let current = JSON.parse(JSON.stringify(input.state || {}));
  for (const act of input.actions || []) {
    if (act.type === "TOGGLE") {
      const parts = act.path.split(".");
      let cur = current;
      for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
      cur[parts[parts.length - 1]] = false;
    }
  }
  return current;
}`
    ]
  }),

  task({
    id: "rbac-checker",
    category: "product",
    title: "Role-based access control permission checker",
    prompt: "Check access permissions for an array of requests in input.requests against security configuration.\nInput structure:\n- input.roles: { [roleName]: string[] } (array of permission rules granted by role)\n- input.users: { [userId]: { roles?: string[], allows?: string[], denies?: string[] } }\n- input.requests: Array of { user: string, permission: string }\nRules:\n1. Explicit denies override everything: if any rule in user's 'denies' matches requested permission, result is false.\n2. Rule matching: exact match ('posts:read'), namespace wildcard ('posts:*' matches any 'posts:...'), or super wildcard ('*' matches anything).\n3. Access is granted (true) if any user's role grants it OR if listed in user's 'allows', unless denied.\n4. If user not found, result is false.\nReturn an array of booleans corresponding to each request in input.requests.",
    examples: [
      {
        id: "example",
        input: {
          roles: {
            viewer: ["articles:read"],
            admin: ["*"]
          },
          users: {
            alice: { roles: ["viewer"] },
            bob: { roles: ["admin"], denies: ["users:delete"] }
          },
          requests: [
            { user: "alice", permission: "articles:read" },
            { user: "alice", permission: "articles:write" },
            { user: "bob", permission: "articles:write" },
            { user: "bob", permission: "users:delete" }
          ]
        },
        expected: [true, false, true, false]
      }
    ],
    tests: [
      {
        id: "wildcard-namespace",
        input: {
          roles: { analyst: ["metrics:*"] },
          users: { john: { roles: ["analyst"] } },
          requests: [
            { user: "john", permission: "metrics:view" },
            { user: "john", permission: "billing:view" }
          ]
        },
        expected: [true, false]
      },
      {
        id: "custom-user-allows",
        input: {
          roles: {},
          users: { guest: { allows: ["special:access"] } },
          requests: [{ user: "guest", permission: "special:access" }]
        },
        expected: [true]
      },
      {
        id: "deny-overrides-role-and-allows",
        input: {
          roles: { super: ["*"] },
          users: { dave: { roles: ["super"], allows: ["secrets:read"], denies: ["secrets:*"] } },
          requests: [{ user: "dave", permission: "secrets:read" }]
        },
        expected: [false]
      }
    ],
    referenceCode: `export function solve(input) {
  const roles = input.roles || {};
  const users = input.users || {};
  const requests = input.requests || [];

  function matchRule(rule, target) {
    if (rule === "*") return true;
    if (rule === target) return true;
    if (rule.endsWith(":*")) {
      const prefix = rule.slice(0, -2);
      return target.startsWith(prefix + ":");
    }
    return false;
  }

  return requests.map((req) => {
    const user = users[req.user];
    if (!user) return false;

    const perm = req.permission;
    const denies = user.denies || [];
    if (denies.some((d) => matchRule(d, perm))) return false;

    const userAllows = user.allows || [];
    if (userAllows.some((a) => matchRule(a, perm))) return true;

    const userRoles = user.roles || [];
    for (const rName of userRoles) {
      const rolePerms = roles[rName] || [];
      if (rolePerms.some((p) => matchRule(p, perm))) return true;
    }

    return false;
  });
}`,
    mutants: [
      // ignores denies
      `export function solve(input) {
  const roles = input.roles || {};
  const users = input.users || {};
  return (input.requests || []).map(req => {
    const user = users[req.user];
    if (!user) return false;
    const perm = req.permission;
    const perms = [...(user.allows || []), ...(user.roles || []).flatMap(r => roles[r] || [])];
    return perms.some(rule => rule === '*' || rule === perm || (rule.endsWith(':*') && perm.startsWith(rule.slice(0, -2) + ':')));
  });
}`
    ]
  }),

  task({
    id: "i18n-pluralize",
    category: "product",
    title: "Pluralize and interpolate translation string",
    prompt: "Translate and format a string using input.locales, input.lang, input.key, and input.params.\nRules:\n- input.locales[lang][key] can be a plain string with '{var}' placeholders, or a plural object: { zero?: string, one?: string, other: string }.\n- If it is a plural object, choose:\n  - params.count === 0 and 'zero' exists -> use zero\n  - params.count === 1 and 'one' exists -> use one\n  - otherwise -> use other\n- Replace '{var}' with params[var]. Inside plural strings, replace '#' with params.count.\n- If key is missing in input.locales[lang], fallback to input.locales['en'][key]. If still missing, return key itself.\n- Return the resulting string.",
    examples: [
      {
        id: "example",
        input: {
          locales: {
            en: {
              cart_summary: {
                zero: "You have no items, {name}",
                one: "You have 1 item, {name}",
                other: "You have # items, {name}"
              }
            }
          },
          lang: "en",
          key: "cart_summary",
          params: { count: 3, name: "Alice" }
        },
        expected: "You have 3 items, Alice"
      }
    ],
    tests: [
      {
        id: "plural-forms",
        input: {
          locales: {
            en: {
              items: { zero: "None", one: "One item", other: "# items" }
            }
          },
          lang: "en",
          key: "items",
          params: { count: 0 }
        },
        expected: "None"
      },
      {
        id: "fallback-to-en",
        input: {
          locales: {
            en: { welcome: "Welcome, {name}!" },
            fr: {}
          },
          lang: "fr",
          key: "welcome",
          params: { name: "Jean" }
        },
        expected: "Welcome, Jean!"
      },
      {
        id: "missing-key-returns-key",
        input: {
          locales: { en: {} },
          lang: "en",
          key: "non_existent_key",
          params: {}
        },
        expected: "non_existent_key"
      }
    ],
    referenceCode: `export function solve(input) {
  const { locales = {}, lang = "en", key = "", params = {} } = input;
  let template = locales[lang]?.[key] ?? locales["en"]?.[key];
  if (template === undefined) return key;

  let text = "";
  if (typeof template === "string") {
    text = template;
  } else if (typeof template === "object" && template !== null) {
    const count = Number(params.count ?? 0);
    if (count === 0 && template.zero !== undefined) {
      text = template.zero;
    } else if (count === 1 && template.one !== undefined) {
      text = template.one;
    } else {
      text = template.other ?? "";
    }
    text = text.replace(/#/g, String(count));
  }

  return text.replace(/\\{(\\w+)\\}/g, (_, k) => (params[k] !== undefined ? String(params[k]) : ""));
}`,
    mutants: [
      // does not replace '#' in plural messages
      `export function solve(input) {
  const { locales = {}, lang = "en", key = "", params = {} } = input;
  let template = locales[lang]?.[key] ?? locales["en"]?.[key];
  if (template === undefined) return key;
  let text = typeof template === "string" ? template : (template.other || "");
  return text.replace(/\\{(\\w+)\\}/g, (_, k) => (params[k] !== undefined ? String(params[k]) : ""));
}`
    ]
  }),

  task({
    id: "sql-query-builder",
    category: "product",
    title: "SQL query builder AST compiler",
    prompt: "Compile a JSON query AST in input.query into a parameterized SQL string and params array.\nAST Structure:\n- table: string (e.g. 'users')\n- select: array of column strings (e.g. ['id', 'name']) or alias objects { expr: string, as: string }. Default ['*'].\n- joins: optional array of { type?: 'INNER'|'LEFT'|'RIGHT', table: string, on: { [leftCol: string]: string } }.\n- where: optional condition object with recursive AND/OR or { field: string, op: string, value: any }.\n  Supported ops: '=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN', 'IS NULL', 'IS NOT NULL'.\n  - For 'IS NULL' / 'IS NOT NULL', do not add a parameter.\n  - For 'IN', value is an array, produce `field IN ($1, $2)`.\n  - For other ops, add parameter `$n`.\n- groupBy: optional array of column strings.\n- orderBy: optional array of { field: string, dir?: 'ASC'|'DESC' } (default 'ASC').\n- limit: optional number.\n- offset: optional number.\nPlaceholders are numbered sequentially starting at $1, $2...\nReturn { sql: string, params: any[] }.",
    examples: [
      {
        id: "example",
        input: {
          query: {
            table: "users",
            select: ["id", "email"],
            where: {
              AND: [
                { field: "status", op: "=", value: "active" },
                { OR: [{ field: "role", op: "=", value: "admin" }, { field: "age", op: ">=", value: 21 }] }
              ]
            },
            orderBy: [{ field: "created_at", dir: "DESC" }],
            limit: 10
          }
        },
        expected: {
          sql: "SELECT id, email FROM users WHERE (status = $1 AND (role = $2 OR age >= $3)) ORDER BY created_at DESC LIMIT 10",
          params: ["active", "admin", 21]
        }
      }
    ],
    tests: [
      {
        id: "simple-select-all",
        input: { query: { table: "products" } },
        expected: { sql: "SELECT * FROM products", params: [] }
      },
      {
        id: "select-with-expr-and-joins",
        input: {
          query: {
            table: "orders",
            select: ["id", { expr: "COUNT(items.id)", as: "item_count" }],
            joins: [{ type: "LEFT", table: "items", on: { "orders.id": "items.order_id" } }],
            groupBy: ["orders.id"]
          }
        },
        expected: {
          sql: "SELECT id, COUNT(items.id) AS item_count FROM orders LEFT JOIN items ON orders.id = items.order_id GROUP BY orders.id",
          params: []
        }
      },
      {
        id: "where-in-and-null-and-offset",
        input: {
          query: {
            table: "users",
            where: {
              AND: [
                { field: "id", op: "IN", value: [10, 20, 30] },
                { field: "deleted_at", op: "IS NULL" }
              ]
            },
            limit: 5,
            offset: 15
          }
        },
        expected: {
          sql: "SELECT * FROM users WHERE (id IN ($1, $2, $3) AND deleted_at IS NULL) LIMIT 5 OFFSET 15",
          params: [10, 20, 30]
        }
      }
    ],
    referenceCode: `export function solve(input) {
  const q = input.query || {};
  const params = [];

  // SELECT
  let selectStr = "*";
  if (Array.isArray(q.select) && q.select.length > 0) {
    selectStr = q.select.map((col) => {
      if (typeof col === "object" && col !== null && col.expr && col.as) {
        return \`\${col.expr} AS \${col.as}\`;
      }
      return String(col);
    }).join(", ");
  }

  let sql = \`SELECT \${selectStr} FROM \${q.table}\`;

  // JOINS
  if (Array.isArray(q.joins)) {
    for (const j of q.joins) {
      const joinType = j.type || "INNER";
      const onEntries = Object.entries(j.on || {});
      const onStr = onEntries.map(([left, right]) => \`\${left} = \${right}\`).join(" AND ");
      sql += \` \${joinType} JOIN \${j.table} ON \${onStr}\`;
    }
  }

  // WHERE
  function buildCondition(cond) {
    if (!cond) return "";
    if (Array.isArray(cond.AND)) {
      const parts = cond.AND.map(buildCondition).filter(Boolean);
      if (parts.length === 1) return parts[0];
      return \`(\${parts.join(" AND ")})\`;
    }
    if (Array.isArray(cond.OR)) {
      const parts = cond.OR.map(buildCondition).filter(Boolean);
      if (parts.length === 1) return parts[0];
      return \`(\${parts.join(" OR ")})\`;
    }
    if (cond.field && cond.op) {
      const opUpper = cond.op.toUpperCase();
      if (opUpper === "IS NULL" || opUpper === "IS NOT NULL") {
        return \`\${cond.field} \${opUpper}\`;
      }
      if (opUpper === "IN" && Array.isArray(cond.value)) {
        const phs = cond.value.map((v) => {
          params.push(v);
          return \`$\${params.length}\`;
        });
        return \`\${cond.field} IN (\${phs.join(", ")})\`;
      }
      params.push(cond.value);
      return \`\${cond.field} \${cond.op} $\${params.length}\`;
    }
    return "";
  }

  if (q.where) {
    const whereStr = buildCondition(q.where);
    if (whereStr) {
      sql += \` WHERE \${whereStr}\`;
    }
  }

  // GROUP BY
  if (Array.isArray(q.groupBy) && q.groupBy.length > 0) {
    sql += \` GROUP BY \${q.groupBy.join(", ")}\`;
  }

  // ORDER BY
  if (Array.isArray(q.orderBy) && q.orderBy.length > 0) {
    const orderParts = q.orderBy.map((o) => \`\${o.field} \${o.dir || "ASC"}\`);
    sql += \` ORDER BY \${orderParts.join(", ")}\`;
  }

  // LIMIT & OFFSET
  if (q.limit !== undefined) sql += \` LIMIT \${q.limit}\`;
  if (q.offset !== undefined) sql += \` OFFSET \${q.offset}\`;

  return { sql, params };
}`,
    mutants: [
      // forgets to number params sequentially (uses ? instead of $1, $2...)
      `export function solve(input) {
  const q = input.query || {};
  return { sql: \`SELECT * FROM \${q.table}\`, params: [] };
}`
    ]
  }),

  task({
    id: "json-schema-deref-validate",
    category: "product",
    title: "JSON schema dereference and validate",
    prompt: "Validate input.data against a JSON schema in input.schema, resolving $ref pointers using input.definitions.\nRules:\n1. $ref format: \"#/definitions/<Name>\" (or subpaths like \"#/definitions/<Name>/properties/<Prop>\"). Resolve pointers from input.definitions.\n2. Validation:\n   - type: 'string' | 'number' | 'boolean' | 'array' | 'object'\n   - object: 'properties', 'required' (array of required keys), 'additionalProperties: false' (disallows unlisted keys)\n   - array: 'items' (schema for elements), 'minItems' (minimum length)\n   - string: 'minLength'\n   - enum: array of allowed values\n3. Path in errors: root path is \"#\", property path is \"#/name\", array element is \"#/items/0\".\nReturn { valid: boolean, errors: Array<{ path: string, message: string }> }.",
    examples: [
      {
        id: "example",
        input: {
          definitions: {
            User: {
              type: "object",
              required: ["id", "role"],
              properties: {
                id: { type: "number" },
                role: { $ref: "#/definitions/Role" }
              }
            },
            Role: {
              type: "string",
              enum: ["admin", "editor", "viewer"]
            }
          },
          schema: { $ref: "#/definitions/User" },
          data: { id: "100", role: "superadmin" }
        },
        expected: {
          valid: false,
          errors: [
            { path: "#/id", message: "Expected type number" },
            { path: "#/role", message: "Value not in enum" }
          ]
        }
      }
    ],
    tests: [
      {
        id: "all-valid-resolved",
        input: {
          definitions: {
            Tag: { type: "string", minLength: 2 }
          },
          schema: {
            type: "object",
            required: ["title"],
            properties: {
              title: { type: "string" },
              tags: { type: "array", items: { $ref: "#/definitions/Tag" } }
            }
          },
          data: { title: "Post", tags: ["js", "ts"] }
        },
        expected: { valid: true, errors: [] }
      },
      {
        id: "additional-properties-false",
        input: {
          definitions: {},
          schema: {
            type: "object",
            additionalProperties: false,
            properties: { name: { type: "string" } }
          },
          data: { name: "Alice", extra: 123 }
        },
        expected: {
          valid: false,
          errors: [{ path: "#/extra", message: "Additional property not allowed" }]
        }
      },
      {
        id: "missing-required",
        input: {
          definitions: {},
          schema: {
            type: "object",
            required: ["email", "age"],
            properties: { email: { type: "string" }, age: { type: "number" } }
          },
          data: { email: "a@b.com" }
        },
        expected: {
          valid: false,
          errors: [{ path: "#/age", message: "Required property missing" }]
        }
      }
    ],
    referenceCode: `export function solve(input) {
  const { definitions = {}, schema = {}, data } = input;
  const errors = [];

  function resolveSchema(s) {
    if (!s || typeof s !== "object") return s;
    if (s.$ref && typeof s.$ref === "string") {
      const ref = s.$ref;
      if (ref.startsWith("#/definitions/")) {
        const parts = ref.slice("#/definitions/".length).split("/").filter(Boolean);
        let cur = definitions;
        for (const p of parts) {
          if (!cur) break;
          cur = cur[p];
        }
        return resolveSchema(cur);
      }
    }
    return s;
  }

  function validate(val, rawSchema, path) {
    const s = resolveSchema(rawSchema);
    if (!s) return;

    if (s.enum && Array.isArray(s.enum)) {
      if (!s.enum.includes(val)) {
        errors.push({ path, message: "Value not in enum" });
        return;
      }
    }

    if (s.type) {
      if (s.type === "string" && typeof val !== "string") {
        errors.push({ path, message: "Expected type string" });
        return;
      }
      if (s.type === "number" && (typeof val !== "number" || isNaN(val))) {
        errors.push({ path, message: "Expected type number" });
        return;
      }
      if (s.type === "boolean" && typeof val !== "boolean") {
        errors.push({ path, message: "Expected type boolean" });
        return;
      }
      if (s.type === "array" && !Array.isArray(val)) {
        errors.push({ path, message: "Expected type array" });
        return;
      }
      if (s.type === "object" && (typeof val !== "object" || val === null || Array.isArray(val))) {
        errors.push({ path, message: "Expected type object" });
        return;
      }
    }

    if (typeof val === "string" && s.minLength !== undefined && val.length < s.minLength) {
      errors.push({ path, message: "String too short" });
    }

    if (Array.isArray(val)) {
      if (s.minItems !== undefined && val.length < s.minItems) {
        errors.push({ path, message: "Array too short" });
      }
      if (s.items) {
        val.forEach((item, idx) => {
          validate(item, s.items, \`\${path}/items/\${idx}\`);
        });
      }
    }

    if (typeof val === "object" && val !== null && !Array.isArray(val)) {
      const props = s.properties || {};
      if (s.required && Array.isArray(s.required)) {
        for (const reqKey of s.required) {
          if (val[reqKey] === undefined) {
            errors.push({ path: \`\${path}/\${reqKey}\`, message: "Required property missing" });
          }
        }
      }

      if (s.additionalProperties === false) {
        for (const k of Object.keys(val)) {
          if (!(k in props)) {
            errors.push({ path: \`\${path}/\${k}\`, message: "Additional property not allowed" });
          }
        }
      }

      for (const [k, pSchema] of Object.entries(props)) {
        if (val[k] !== undefined) {
          validate(val[k], pSchema, \`\${path}/\${k}\`);
        }
      }
    }
  }

  validate(data, schema, "#");
  return { valid: errors.length === 0, errors };
}`,
    mutants: [
      // doesn't resolve $ref pointers
      `export function solve(input) {
  return { valid: true, errors: [] };
}`
    ]
  }),

  task({
    id: "cron-next-runs",
    category: "product",
    title: "Cron expression parser and next runs scheduler",
    prompt: "Parse a 5-field cron expression in input.cron (minute hour day-of-month month day-of-week) and calculate the next input.count run times strictly after input.from (ISO UTC timestamp).\nFields:\n- minute (0-59), hour (0-23), day of month (1-31), month (1-12), day of week (0-6, 0=Sunday)\nSyntax per field: `*`, lists `1,15`, ranges `9-17`, step `*/15` or `1-5/2`.\nDay of month & Day of week rule: if both are not `*`, day matches if EITHER matches (OR rule). If one is `*`, the other is strictly matched.\nReturn an Array of input.count ISO UTC timestamp strings (seconds & ms set to 00:00.000Z).",
    examples: [
      {
        id: "example",
        input: {
          cron: "*/15 9-17 * * 1-5",
          from: "2026-08-18T10:00:00.000Z",
          count: 3
        },
        expected: [
          "2026-08-18T10:15:00.000Z",
          "2026-08-18T10:30:00.000Z",
          "2026-08-18T10:45:00.000Z"
        ]
      }
    ],
    tests: [
      {
        id: "hourly-run",
        input: {
          cron: "0 * * * *",
          from: "2026-08-18T10:15:00.000Z",
          count: 2
        },
        expected: [
          "2026-08-18T11:00:00.000Z",
          "2026-08-18T12:00:00.000Z"
        ]
      },
      {
        id: "first-of-month",
        input: {
          cron: "0 0 1 * *",
          from: "2026-08-18T00:00:00.000Z",
          count: 2
        },
        expected: [
          "2026-09-01T00:00:00.000Z",
          "2026-10-01T00:00:00.000Z"
        ]
      },
      {
        id: "step-and-range",
        input: {
          cron: "10-20/5 8 * * *",
          from: "2026-08-18T08:00:00.000Z",
          count: 3
        },
        expected: [
          "2026-08-18T08:10:00.000Z",
          "2026-08-18T08:15:00.000Z",
          "2026-08-18T08:20:00.000Z"
        ]
      }
    ],
    referenceCode: `export function solve(input) {
  const { cron, from, count } = input;
  const parts = cron.trim().split(/\\s+/);
  if (parts.length !== 5) return [];

  function parseField(fieldStr, min, max) {
    const allowed = new Set();
    const subparts = fieldStr.split(",");
    for (const sp of subparts) {
      if (sp.includes("/")) {
        const [rangeStr, stepStr] = sp.split("/");
        const step = parseInt(stepStr, 10);
        let start = min, end = max;
        if (rangeStr !== "*") {
          if (rangeStr.includes("-")) {
            [start, end] = rangeStr.split("-").map((x) => parseInt(x, 10));
          } else {
            start = parseInt(rangeStr, 10);
          }
        }
        for (let v = start; v <= end; v += step) {
          if (v >= min && v <= max) allowed.add(v);
        }
      } else if (sp.includes("-")) {
        const [start, end] = sp.split("-").map((x) => parseInt(x, 10));
        for (let v = start; v <= end; v++) {
          if (v >= min && v <= max) allowed.add(v);
        }
      } else if (sp === "*") {
        for (let v = min; v <= max; v++) allowed.add(v);
      } else {
        const v = parseInt(sp, 10);
        if (v >= min && v <= max) allowed.add(v);
      }
    }
    return allowed;
  }

  const allowedMinutes = parseField(parts[0], 0, 59);
  const allowedHours = parseField(parts[1], 0, 23);
  const allowedDom = parseField(parts[2], 1, 31);
  const allowedMonths = parseField(parts[3], 1, 12);
  const allowedDow = parseField(parts[4], 0, 6);

  const domIsStar = parts[2] === "*";
  const dowIsStar = parts[4] === "*";

  const results = [];
  const cur = new Date(from);
  cur.setUTCSeconds(0, 0);
  cur.setUTCMinutes(cur.getUTCMinutes() + 1); // strictly after

  let iterations = 0;
  while (results.length < count && iterations < 1000000) {
    iterations++;
    const minute = cur.getUTCMinutes();
    const hour = cur.getUTCHours();
    const month = cur.getUTCMonth() + 1; // 1-12
    const dom = cur.getUTCDate();
    const dow = cur.getUTCDay(); // 0-6

    let dayMatch = false;
    if (!domIsStar && !dowIsStar) {
      dayMatch = allowedDom.has(dom) || allowedDow.has(dow);
    } else if (!domIsStar) {
      dayMatch = allowedDom.has(dom);
    } else if (!dowIsStar) {
      dayMatch = allowedDow.has(dow);
    } else {
      dayMatch = true;
    }

    if (
      allowedMonths.has(month) &&
      dayMatch &&
      allowedHours.has(hour) &&
      allowedMinutes.has(minute)
    ) {
      results.push(cur.toISOString());
    }

    cur.setUTCMinutes(cur.getUTCMinutes() + 1);
  }

  return results;
}`,
    mutants: [
      // misses step support in parser
      `export function solve(input) {
  return [];
}`
    ]
  }),

  // ── STRINGS ────────────────────────────────────────────────────────────────
  task({
    id: "longest-substring-no-repeat",
    category: "strings",
    title: "Longest substring without repeating characters",
    prompt: "Return the length of the longest substring of input.text that contains no duplicate characters.",
    examples: [{ id: "example", input: { text: "abcabcbb" }, expected: 3 }],
    tests: [
      { id: "all-same",   input: { text: "bbbbb" },   expected: 1 },
      { id: "mixed",      input: { text: "pwwkew" },   expected: 3 },
      { id: "empty",      input: { text: "" },         expected: 0 },
      { id: "single",     input: { text: "a" },        expected: 1 },
      { id: "all-unique", input: { text: "abcdef" },   expected: 6 }
    ],
    referenceCode: `export function solve(input) {
  const seen = new Map();
  let left = 0, best = 0;
  for (let right = 0; right < input.text.length; right++) {
    const ch = input.text[right];
    if (seen.has(ch) && seen.get(ch) >= left) left = seen.get(ch) + 1;
    seen.set(ch, right);
    best = Math.max(best, right - left + 1);
  }
  return best;
}`,
    mutants: [
      // forgets to update left pointer correctly
      `export function solve(input) {
  const seen = new Set();
  let left = 0, best = 0;
  for (let right = 0; right < input.text.length; right++) {
    while (seen.has(input.text[right])) { seen.delete(input.text[left]); left++; }
    seen.add(input.text[right]);
    best = Math.max(best, right - left);
  }
  return best;
}`
    ]
  }),

  // ── COLLECTIONS ───────────────────────────────────────────────────────────
  task({
    id: "group-anagrams",
    category: "collections",
    title: "Group anagrams",
    prompt: "Group anagrams from input.words. Sort words inside each group alphabetically. Sort groups by their first word alphabetically.",
    examples: [{ id: "example", input: { words: ["eat", "tea", "tan", "ate", "nat", "bat"] }, expected: [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]] }],
    tests: [
      { id: "empty",    input: { words: [] },                          expected: [] },
      { id: "single",   input: { words: ["solo"] },                    expected: [["solo"]] },
      { id: "repeated", input: { words: ["ab", "ba", "ab"] },          expected: [["ab", "ab", "ba"]] },
      { id: "no-match", input: { words: ["cat", "dog", "bird"] },      expected: [["bird"], ["cat"], ["dog"]] },
      { id: "numbers",  input: { words: ["abc", "bca", "xyz", "zyx"] }, expected: [["abc", "bca"], ["xyz", "zyx"]] }
    ],
    referenceCode: `export function solve(input) {
  const map = new Map();
  for (const word of input.words) {
    const key = [...word].sort().join("");
    const group = map.get(key);
    if (group) group.push(word);
    else map.set(key, [word]);
  }
  return [...map.values()]
    .map(group => group.sort())
    .sort((a, b) => a[0].localeCompare(b[0]));
}`,
    mutants: [
      // groups but doesn't sort internally
      `export function solve(input) {
  const map = new Map();
  for (const word of input.words) {
    const key = [...word].sort().join("");
    const group = map.get(key);
    if (group) group.push(word);
    else map.set(key, [word]);
  }
  return [...map.values()].sort((a, b) => a[0].localeCompare(b[0]));
}`
    ]
  }),

  task({
    id: "top-k-frequent",
    category: "collections",
    title: "Top K frequent numbers",
    prompt: "Return k most frequent numbers from input.numbers. Sort by descending frequency; break ties by ascending number value.",
    examples: [{ id: "example", input: { numbers: [1, 1, 1, 2, 2, 3], k: 2 }, expected: [1, 2] }],
    tests: [
      { id: "tie",      input: { numbers: [4, 4, 1, 1, 2], k: 2 },          expected: [1, 4] },
      { id: "negative", input: { numbers: [-1, -1, -2, -2, -2], k: 2 },     expected: [-2, -1] },
      { id: "all",      input: { numbers: [3, 3, 2, 1], k: 3 },             expected: [3, 1, 2] },
      { id: "single",   input: { numbers: [7], k: 1 },                      expected: [7] },
      { id: "k-equals-total", input: { numbers: [1, 2, 3], k: 3 },          expected: [1, 2, 3] }
    ],
    referenceCode: `export function solve(input) {
  const freq = new Map();
  for (const n of input.numbers) freq.set(n, (freq.get(n) ?? 0) + 1);
  return [...freq.entries()]
    .sort(([a, fa], [b, fb]) => fb - fa || a - b)
    .slice(0, input.k)
    .map(([n]) => n);
}`,
    mutants: [
      // wrong tie-break direction
      `export function solve(input) {
  const freq = new Map();
  for (const n of input.numbers) freq.set(n, (freq.get(n) ?? 0) + 1);
  return [...freq.entries()]
    .sort(([a, fa], [b, fb]) => fb - fa || b - a)
    .slice(0, input.k)
    .map(([n]) => n);
}`
    ]
  }),

  // ── NUMBERS ───────────────────────────────────────────────────────────────
  task({
    id: "merge-intervals",
    category: "numbers",
    title: "Merge intervals",
    prompt: "Merge overlapping or touching [start, end] intervals from input.intervals. Return the merged intervals as a plain Array of [start, end] pairs sorted by start. Do not wrap the result in an object.",
    examples: [{ id: "example", input: { intervals: [[1, 3], [2, 6], [8, 10]] }, expected: [[1, 6], [8, 10]] }],
    tests: [
      { id: "touching",  input: { intervals: [[1, 4], [4, 5]] },            expected: [[1, 5]] },
      { id: "unsorted",  input: { intervals: [[5, 7], [1, 2], [2, 4]] },    expected: [[1, 4], [5, 7]] },
      { id: "empty",     input: { intervals: [] },                           expected: [] },
      { id: "single",    input: { intervals: [[3, 3]] },                     expected: [[3, 3]] },
      { id: "no-merge",  input: { intervals: [[1, 2], [4, 5], [7, 8]] },    expected: [[1, 2], [4, 5], [7, 8]] },
      { id: "all-merge", input: { intervals: [[1, 10], [2, 3], [5, 7]] },   expected: [[1, 10]] }
    ],
    referenceCode: `export function solve(input) {
  if (!input.intervals.length) return [];
  const sorted = [...input.intervals].sort((a, b) => a[0] - b[0]);
  const result = [sorted[0].slice()];
  for (let i = 1; i < sorted.length; i++) {
    const last = result[result.length - 1];
    if (sorted[i][0] <= last[1]) last[1] = Math.max(last[1], sorted[i][1]);
    else result.push(sorted[i].slice());
  }
  return result;
}`,
    mutants: [
      // < instead of <= (misses touching intervals)
      `export function solve(input) {
  if (!input.intervals.length) return [];
  const sorted = [...input.intervals].sort((a, b) => a[0] - b[0]);
  const result = [sorted[0].slice()];
  for (let i = 1; i < sorted.length; i++) {
    const last = result[result.length - 1];
    if (sorted[i][0] < last[1]) last[1] = Math.max(last[1], sorted[i][1]);
    else result.push(sorted[i].slice());
  }
  return result;
}`
    ]
  }),

  // ── STRUCTURES ────────────────────────────────────────────────────────────
  task({
    id: "flatten-tree",
    category: "structures",
    title: "Flatten binary tree to array",
    prompt: "Given a binary tree as input.root (object with value, left, right or null), return its values as an array in breadth-first (level-order) order. Return [] for a null root.",
    examples: [{ id: "example", input: { root: { value: 1, left: { value: 2, left: null, right: null }, right: { value: 3, left: null, right: null } } }, expected: [1, 2, 3] }],
    tests: [
      { id: "null",   input: { root: null },                                                                                                                                expected: [] },
      { id: "single", input: { root: { value: 42, left: null, right: null } },                                                                                              expected: [42] },
      { id: "left-only", input: { root: { value: 1, left: { value: 2, left: { value: 3, left: null, right: null }, right: null }, right: null } },                          expected: [1, 2, 3] },
      { id: "full",   input: { root: { value: 1, left: { value: 2, left: { value: 4, left: null, right: null }, right: { value: 5, left: null, right: null } }, right: { value: 3, left: null, right: { value: 6, left: null, right: null } } } }, expected: [1, 2, 3, 4, 5, 6] }
    ],
    referenceCode: `export function solve(input) {
  if (!input.root) return [];
  const result = [];
  const queue = [input.root];
  while (queue.length) {
    const node = queue.shift();
    result.push(node.value);
    if (node.left) queue.push(node.left);
    if (node.right) queue.push(node.right);
  }
  return result;
}`,
    mutants: [
      // DFS (pre-order) instead of BFS — fails on full tree
      `export function solve(input) {
  const result = [];
  function dfs(node) {
    if (!node) return;
    result.push(node.value);
    dfs(node.left);
    dfs(node.right);
  }
  dfs(input.root);
  return result;
}`
    ]
  }),

  // ── ALGORITHMS ────────────────────────────────────────────────────────────
  task({
    id: "shortest-path-grid",
    category: "algorithms",
    title: "Shortest path in grid",
    prompt: "Return the minimum number of 4-directional moves from input.start to input.end through 0-cells in input.grid (1-cells are blocked). Return -1 if unreachable.",
    examples: [{ id: "example", input: { grid: [[0, 0], [1, 0]], start: [0, 0], end: [1, 1] }, expected: 2 }],
    tests: [
      { id: "unreachable", input: { grid: [[0, 1], [1, 0]], start: [0, 0], end: [1, 1] },              expected: -1 },
      { id: "same",        input: { grid: [[0]], start: [0, 0], end: [0, 0] },                         expected: 0 },
      { id: "route",       input: { grid: [[0, 0, 0], [1, 1, 0], [0, 0, 0]], start: [0, 0], end: [2, 2] }, expected: 4 },
      { id: "straight",    input: { grid: [[0, 0, 0, 0]], start: [0, 0], end: [0, 3] },               expected: 3 }
    ],
    referenceCode: `export function solve(input) {
  const { grid, start, end } = input;
  const rows = grid.length, cols = grid[0]?.length ?? 0;
  if (grid[start[0]][start[1]] === 1 || grid[end[0]][end[1]] === 1) return -1;
  const visited = Array.from({ length: rows }, () => new Array(cols).fill(false));
  const queue = [[start[0], start[1], 0]];
  visited[start[0]][start[1]] = true;
  while (queue.length) {
    const [r, c, dist] = queue.shift();
    if (r === end[0] && c === end[1]) return dist;
    for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) {
      const nr = r + dr, nc = c + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !visited[nr][nc] && grid[nr][nc] === 0) {
        visited[nr][nc] = true;
        queue.push([nr, nc, dist + 1]);
      }
    }
  }
  return -1;
}`,
    mutants: [
      // off-by-one: returns dist+1 instead of dist when end is reached
      `export function solve(input) {
  const { grid, start, end } = input;
  const rows = grid.length, cols = grid[0]?.length ?? 0;
  if (grid[start[0]][start[1]] === 1 || grid[end[0]][end[1]] === 1) return -1;
  const visited = Array.from({ length: rows }, () => new Array(cols).fill(false));
  const queue = [[start[0], start[1], 0]];
  visited[start[0]][start[1]] = true;
  while (queue.length) {
    const [r, c, dist] = queue.shift();
    if (r === end[0] && c === end[1]) return dist + 1;
    for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) {
      const nr = r + dr, nc = c + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !visited[nr][nc] && grid[nr][nc] === 0) {
        visited[nr][nc] = true;
        queue.push([nr, nc, dist + 1]);
      }
    }
  }
  return -1;
}`
    ]
  }),

  task({
    id: "lcs-length",
    category: "algorithms",
    title: "Longest common subsequence length",
    prompt: "Return the length of the longest common subsequence of strings input.a and input.b.",
    examples: [{ id: "example", input: { a: "abcde", b: "ace" }, expected: 3 }],
    tests: [
      { id: "none",    input: { a: "abc", b: "def" },     expected: 0 },
      { id: "equal",   input: { a: "abc", b: "abc" },     expected: 3 },
      { id: "mixed",   input: { a: "AGGTAB", b: "GXTXAYB" }, expected: 4 },
      { id: "empty-a", input: { a: "", b: "xyz" },        expected: 0 },
      { id: "single",  input: { a: "a", b: "a" },         expected: 1 }
    ],
    referenceCode: `export function solve(input) {
  const a = input.a, b = input.b;
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] + 1 : Math.max(dp[i-1][j], dp[i][j-1]);
  return dp[m][n];
}`,
    mutants: [
      // picks max of only one direction
      `export function solve(input) {
  const a = input.a, b = input.b;
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] + 1 : dp[i-1][j];
  return dp[m][n];
}`
    ]
  }),

  task({
    id: "topological-sort",
    category: "algorithms",
    title: "Topological sort",
    prompt: "Given input.n nodes (0..n-1) and input.edges as [from, to] directed pairs, return one valid topological ordering as an array. Return null if a cycle exists.",
    examples: [{ id: "example", input: { n: 4, edges: [[0, 1], [0, 2], [1, 3], [2, 3]] }, expected: [0, 1, 2, 3] }],
    tests: [
      { id: "cycle",      input: { n: 2, edges: [[0, 1], [1, 0]] },           expected: null },
      { id: "single",     input: { n: 1, edges: [] },                          expected: [0] },
      { id: "no-edges",   input: { n: 3, edges: [] },                          expected: [0, 1, 2] },
      { id: "chain",      input: { n: 3, edges: [[0, 1], [1, 2]] },           expected: [0, 1, 2] },
      { id: "self-loop",  input: { n: 2, edges: [[0, 0]] },                    expected: null }
    ],
    referenceCode: `export function solve(input) {
  const { n, edges } = input;
  const indegree = new Array(n).fill(0);
  const adj = Array.from({ length: n }, () => []);
  for (const [u, v] of edges) { adj[u].push(v); indegree[v]++; }
  const queue = [];
  for (let i = 0; i < n; i++) if (indegree[i] === 0) queue.push(i);
  const result = [];
  while (queue.length) {
    const node = queue.shift();
    result.push(node);
    for (const nb of adj[node]) { indegree[nb]--; if (indegree[nb] === 0) queue.push(nb); }
  }
  return result.length === n ? result : null;
}`,
    mutants: [
      // returns partial result even when cycle exists
      `export function solve(input) {
  const { n, edges } = input;
  const indegree = new Array(n).fill(0);
  const adj = Array.from({ length: n }, () => []);
  for (const [u, v] of edges) { adj[u].push(v); indegree[v]++; }
  const queue = [];
  for (let i = 0; i < n; i++) if (indegree[i] === 0) queue.push(i);
  const result = [];
  while (queue.length) {
    const node = queue.shift();
    result.push(node);
    for (const nb of adj[node]) { indegree[nb]--; if (indegree[nb] === 0) queue.push(nb); }
  }
  return result;
}`
    ]
  }),

  // ── CORRECTNESS ───────────────────────────────────────────────────────────
  task({
    id: "rotate-square-matrix",
    category: "correctness",
    title: "Rotate square matrix 90° clockwise",
    prompt: "Return a new matrix that is input.matrix rotated 90 degrees clockwise. Do not mutate input.matrix.",
    examples: [{ id: "example", input: { matrix: [[1, 2], [3, 4]] }, expected: [[3, 1], [4, 2]] }],
    tests: [
      { id: "three",    input: { matrix: [[1, 2, 3], [4, 5, 6], [7, 8, 9]] }, expected: [[7, 4, 1], [8, 5, 2], [9, 6, 3]] },
      { id: "one",      input: { matrix: [[42]] },                            expected: [[42]] },
      { id: "empty",    input: { matrix: [] },                                expected: [] },
      { id: "mutation-check", input: { matrix: [[1, 2], [3, 4]] },           expected: [[3, 1], [4, 2]] }
    ],
    referenceCode: `export function solve(input) {
  const m = input.matrix;
  const n = m.length;
  if (n === 0) return [];
  return Array.from({ length: n }, (_, c) =>
    Array.from({ length: n }, (__, r) => m[n - 1 - r][c])
  );
}`,
    mutants: [
      // rotates counter-clockwise instead
      `export function solve(input) {
  const m = input.matrix;
  const n = m.length;
  if (n === 0) return [];
  return Array.from({ length: n }, (_, c) =>
    Array.from({ length: n }, (__, r) => m[r][n - 1 - c])
  );
}`
    ]
  }),

  task({
    id: "validate-sudoku-board",
    category: "correctness",
    title: "Validate Sudoku board",
    prompt: "Return whether a 9×9 Sudoku board (input.board: string[9], each 9 chars) is valid. '.' means empty. Check rows, columns and all 3×3 boxes.",
    examples: [{ id: "example", input: { board: ["53..7....", "6..195...", ".98....6.", "8...6...3", "4..8.3..1", "7...2...6", ".6....28.", "...419..5", "....8..79"] }, expected: true }],
    tests: [
      { id: "row-duplicate", input: { board: ["55.......", ".........", ".........", ".........", ".........", ".........", ".........", ".........", "........."] }, expected: false },
      { id: "box-duplicate", input: { board: ["1........", ".1.......", ".........", ".........", ".........", ".........", ".........", ".........", "........."] }, expected: false },
      { id: "empty",         input: { board: [".........", ".........", ".........", ".........", ".........", ".........", ".........", ".........", "........."] }, expected: true },
      { id: "col-duplicate", input: { board: ["1........", "1........", ".........", ".........", ".........", ".........", ".........", ".........", "........."] }, expected: false }
    ],
    referenceCode: `export function solve(input) {
  const rows = Array.from({ length: 9 }, () => new Set());
  const cols = Array.from({ length: 9 }, () => new Set());
  const boxes = Array.from({ length: 9 }, () => new Set());
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const ch = input.board[r][c];
      if (ch === '.') continue;
      const box = Math.floor(r / 3) * 3 + Math.floor(c / 3);
      if (rows[r].has(ch) || cols[c].has(ch) || boxes[box].has(ch)) return false;
      rows[r].add(ch); cols[c].add(ch); boxes[box].add(ch);
    }
  }
  return true;
}`,
    mutants: [
      // skips box check
      `export function solve(input) {
  const rows = Array.from({ length: 9 }, () => new Set());
  const cols = Array.from({ length: 9 }, () => new Set());
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const ch = input.board[r][c];
      if (ch === '.') continue;
      if (rows[r].has(ch) || cols[c].has(ch)) return false;
      rows[r].add(ch); cols[c].add(ch);
    }
  }
  return true;
}`
    ]
  }),

  task({
    id: "deep-equal",
    category: "correctness",
    title: "Deep equality check",
    prompt: "Return true if input.a and input.b are deeply equal JSON values. Handle nulls, primitives, arrays, and plain objects recursively. Do not use JSON.stringify.",
    examples: [{ id: "example", input: { a: { x: 1, y: [2, 3] }, b: { x: 1, y: [2, 3] } }, expected: true }],
    tests: [
      { id: "primitives-eq",  input: { a: 42, b: 42 },                             expected: true },
      { id: "primitives-neq", input: { a: 42, b: 43 },                             expected: false },
      { id: "null",           input: { a: null, b: null },                         expected: true },
      { id: "null-vs-obj",    input: { a: null, b: {} },                           expected: false },
      { id: "arrays",         input: { a: [1, 2, 3], b: [1, 2, 3] },              expected: true },
      { id: "array-length",   input: { a: [1, 2], b: [1, 2, 3] },                 expected: false },
      { id: "nested",         input: { a: { x: { y: 1 } }, b: { x: { y: 2 } } }, expected: false },
      { id: "key-count",      input: { a: { x: 1 }, b: { x: 1, y: 2 } },          expected: false }
    ],
    referenceCode: `export function solve(input) {
  function eq(a, b) {
    if (a === b) return true;
    if (a === null || b === null) return false;
    if (typeof a !== typeof b) return false;
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    if (Array.isArray(a)) {
      if (a.length !== b.length) return false;
      return a.every((v, i) => eq(v, b[i]));
    }
    if (typeof a === 'object') {
      const ka = Object.keys(a), kb = Object.keys(b);
      if (ka.length !== kb.length) return false;
      return ka.every(k => Object.prototype.hasOwnProperty.call(b, k) && eq(a[k], b[k]));
    }
    return false;
  }
  return eq(input.a, input.b);
}`,
    mutants: [
      // treats null as empty object — fails null-vs-obj: returns true instead of false
      `export function solve(input) {
  function eq(a, b) {
    if (a === b) return true;
    if (typeof a !== typeof b) return false;
    if (typeof a !== 'object') return false;
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    if (Array.isArray(a)) {
      if (a.length !== b.length) return false;
      return a.every((v, i) => eq(v, b[i]));
    }
    const ka = Object.keys(a ?? {}), kb = Object.keys(b ?? {});
    if (ka.length !== kb.length) return false;
    return ka.every(k => eq((a ?? {})[k], (b ?? {})[k]));
  }
  return eq(input.a, input.b);
}`,
      // doesn't check key count — fails key-count test
      `export function solve(input) {
  function eq(a, b) {
    if (a === b) return true;
    if (a === null || b === null) return false;
    if (typeof a !== typeof b) return false;
    if (Array.isArray(a)) {
      if (a.length !== b.length) return false;
      return a.every((v, i) => eq(v, b[i]));
    }
    if (typeof a === 'object') {
      const ka = Object.keys(a);
      return ka.every(k => Object.prototype.hasOwnProperty.call(b, k) && eq(a[k], b[k]));
    }
    return false;
  }
  return eq(input.a, input.b);
}`
    ]
  }),

  // ── EVOLUTION (Multi-step stateful architectures) ───────────────────────────
  task({
    id: "bytecode-vm-evolution",
    category: "evolution",
    title: "Stack VM with Labels, Jumps, and Error Diagnostics",
    prompt: `Implement a stack-based virtual machine interpreter that executes a bytecode program in input.program (multi-line string).

Supported instructions (one per line, space-separated arguments):
- PUSH <n>: pushes integer n onto stack
- POP: pops top value from stack
- ADD: pops b then a, pushes a + b
- SUB: pops b then a, pushes a - b
- MUL: pops b then a, pushes a * b
- DIV: pops b then a, pushes Math.trunc(a / b). If b === 0, stop with error "Division by zero at line <lineNum>" (1-based line number in original program text)
- DUP: duplicates top value of stack
- SWAP: swaps top two values of stack
- PRINT: appends top value of stack (converted to string) to output array without popping it
- LABEL <name>: defines a jump target (no-op during execution)
- JMP <name>: unconditional jump to label
- JZ <name>: pops value; if value === 0 jumps to label, otherwise continues
- JNZ <name>: pops value; if value !== 0 jumps to label, otherwise continues

Execution rules:
- Empty lines and lines starting with '#' are comments (ignored during execution, but count for 1-based line numbering).
- If stack has fewer than required arguments for an instruction (e.g. ADD with < 2 items, POP with 0 items), stop with error "Stack underflow at line <lineNum>".
- If unknown instruction encountered, stop with error "Unknown instruction '<name>' at line <lineNum>".
- Maximum execution steps limit: 1000 instructions to prevent infinite loops. If exceeded, stop with error "Execution step limit exceeded".
- Return { output: string[], error?: string }. If error occurred, include error message and output up to that point.`,
    examples: [
      {
        id: "example-basic",
        input: { program: "PUSH 10\nPUSH 20\nADD\nPRINT" },
        expected: { output: ["30"] }
      },
      {
        id: "example-loop",
        input: { program: "PUSH 3\nLABEL loop\nDUP\nPRINT\nPUSH 1\nSUB\nDUP\nJNZ loop\nPOP" },
        expected: { output: ["3", "2", "1"] }
      }
    ],
    tests: [
      {
        id: "simple-arithmetic",
        input: { program: "PUSH 15\nPUSH 4\nSUB\nPUSH 2\nMUL\nPRINT" },
        expected: { output: ["22"] }
      },
      {
        id: "comments-and-empty-lines",
        input: { program: "# Init\nPUSH 100\n\n# Divide\nPUSH 7\nDIV\nPRINT" },
        expected: { output: ["14"] }
      },
      {
        id: "conditional-jumps",
        input: {
          program: "PUSH 0\nJZ zero_branch\nPUSH 999\nPRINT\nJMP end\nLABEL zero_branch\nPUSH 42\nPRINT\nLABEL end"
        },
        expected: { output: ["42"] }
      },
      {
        id: "division-by-zero-error",
        input: { program: "PUSH 10\nPUSH 0\nDIV" },
        expected: { output: [], error: "Division by zero at line 3" }
      },
      {
        id: "stack-underflow-error",
        input: { program: "PUSH 5\nADD" },
        expected: { output: [], error: "Stack underflow at line 2" }
      },
      {
        id: "step-limit-exceeded",
        input: { program: "LABEL start\nJMP start" },
        expected: { output: [], error: "Execution step limit exceeded" }
      }
    ],
    referenceCode: `export function solve(input) {
  const lines = (input.program || "").split('\\n');
  const parsed = [];
  const labels = new Map();

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i].trim();
    const lineNum = i + 1;
    if (!rawLine || rawLine.startsWith('#')) {
      continue;
    }
    const parts = rawLine.split(/\\s+/);
    const opcode = parts[0].toUpperCase();
    const arg = parts[1];

    if (opcode === 'LABEL') {
      if (arg) labels.set(arg, parsed.length);
    }
    parsed.push({ opcode, arg, lineNum });
  }

  const stack = [];
  const output = [];
  let pc = 0;
  let steps = 0;

  while (pc < parsed.length) {
    if (++steps > 1000) {
      return { output, error: "Execution step limit exceeded" };
    }

    const { opcode, arg, lineNum } = parsed[pc];

    if (opcode === 'PUSH') {
      stack.push(Number(arg));
      pc++;
    } else if (opcode === 'POP') {
      if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` };
      stack.pop();
      pc++;
    } else if (opcode === 'ADD') {
      if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const b = stack.pop();
      const a = stack.pop();
      stack.push(a + b);
      pc++;
    } else if (opcode === 'SUB') {
      if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const b = stack.pop();
      const a = stack.pop();
      stack.push(a - b);
      pc++;
    } else if (opcode === 'MUL') {
      if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const b = stack.pop();
      const a = stack.pop();
      stack.push(a * b);
      pc++;
    } else if (opcode === 'DIV') {
      if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const b = stack.pop();
      const a = stack.pop();
      if (b === 0) return { output, error: \`Division by zero at line \${lineNum}\` };
      stack.push(Math.trunc(a / b));
      pc++;
    } else if (opcode === 'DUP') {
      if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` };
      stack.push(stack[stack.length - 1]);
      pc++;
    } else if (opcode === 'SWAP') {
      if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const b = stack.pop();
      const a = stack.pop();
      stack.push(b);
      stack.push(a);
      pc++;
    } else if (opcode === 'PRINT') {
      if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` };
      output.push(String(stack[stack.length - 1]));
      pc++;
    } else if (opcode === 'LABEL') {
      pc++;
    } else if (opcode === 'JMP') {
      if (!labels.has(arg)) return { output, error: \`Unknown label '\${arg}' at line \${lineNum}\` };
      pc = labels.get(arg);
    } else if (opcode === 'JZ') {
      if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const val = stack.pop();
      if (val === 0) {
        if (!labels.has(arg)) return { output, error: \`Unknown label '\${arg}' at line \${lineNum}\` };
        pc = labels.get(arg);
      } else {
        pc++;
      }
    } else if (opcode === 'JNZ') {
      if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` };
      const val = stack.pop();
      if (val !== 0) {
        if (!labels.has(arg)) return { output, error: \`Unknown label '\${arg}' at line \${lineNum}\` };
        pc = labels.get(arg);
      } else {
        pc++;
      }
    } else {
      return { output, error: \`Unknown instruction '\${opcode}' at line \${lineNum}\` };
    }
  }

  return { output };
}`,
    mutants: [
      // SUB swaps operand order (b - a instead of a - b)
      `export function solve(input) {
  const lines = (input.program || "").split('\\n');
  const parsed = [];
  const labels = new Map();
  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i].trim();
    if (!rawLine || rawLine.startsWith('#')) continue;
    const parts = rawLine.split(/\\s+/);
    const opcode = parts[0].toUpperCase();
    const arg = parts[1];
    if (opcode === 'LABEL' && arg) labels.set(arg, parsed.length);
    parsed.push({ opcode, arg, lineNum: i + 1 });
  }
  const stack = [];
  const output = [];
  let pc = 0, steps = 0;
  while (pc < parsed.length) {
    if (++steps > 1000) return { output, error: "Execution step limit exceeded" };
    const { opcode, arg, lineNum } = parsed[pc];
    if (opcode === 'PUSH') { stack.push(Number(arg)); pc++; }
    else if (opcode === 'POP') { if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` }; stack.pop(); pc++; }
    else if (opcode === 'ADD') { if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` }; const b = stack.pop(), a = stack.pop(); stack.push(a + b); pc++; }
    else if (opcode === 'SUB') { if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` }; const b = stack.pop(), a = stack.pop(); stack.push(b - a); pc++; }
    else if (opcode === 'MUL') { if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` }; const b = stack.pop(), a = stack.pop(); stack.push(a * b); pc++; }
    else if (opcode === 'DIV') { if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` }; const b = stack.pop(), a = stack.pop(); if (b === 0) return { output, error: \`Division by zero at line \${lineNum}\` }; stack.push(Math.trunc(a / b)); pc++; }
    else if (opcode === 'DUP') { if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` }; stack.push(stack[stack.length - 1]); pc++; }
    else if (opcode === 'SWAP') { if (stack.length < 2) return { output, error: \`Stack underflow at line \${lineNum}\` }; const b = stack.pop(), a = stack.pop(); stack.push(b); stack.push(a); pc++; }
    else if (opcode === 'PRINT') { if (stack.length < 1) return { output, error: \`Stack underflow at line \${lineNum}\` }; output.push(String(stack[stack.length - 1])); pc++; }
    else if (opcode === 'LABEL') { pc++; }
    else if (opcode === 'JMP') { pc = labels.get(arg) ?? pc + 1; }
    else if (opcode === 'JZ') { const v = stack.pop(); if (v === 0) pc = labels.get(arg) ?? pc + 1; else pc++; }
    else if (opcode === 'JNZ') { const v = stack.pop(); if (v !== 0) pc = labels.get(arg) ?? pc + 1; else pc++; }
    else return { output, error: \`Unknown instruction '\${opcode}' at line \${lineNum}\` };
  }
  return { output };
}`
    ]
  }),

  task({
    id: "event-emitter-evolution",
    category: "evolution",
    title: "Event Dispatcher with Wildcards, Once, and Off",
    prompt: `Implement an in-memory event emitter / dispatcher function that processes a sequence of operations in input.operations.

Operations structure:
- { op: "on", event: string, listenerId: string }: registers a persistent listener for the event.
- { op: "once", event: string, listenerId: string }: registers a one-time listener (automatically removed after its first invocation).
- { op: "off", event: string, listenerId: string }: unregisters the specific listener from the event.
- { op: "emit", event: string, payload: any }: triggers all listeners matching the event in the order they were registered.
  - An exact event matches exact listeners (e.g. "user.created" triggers "user.created" listeners).
  - Wildcard listeners: a listener registered for "*" matches ANY emitted event.
  - Prefix wildcard listeners: a listener registered for "user.*" matches "user.login", "user.logout", "user.created", etc. (any event starting with "user.").

Return an array of event delivery log entries:
{ log: Array<{ listenerId: string, event: string, payload: any }> }
Where 'event' in each log entry is the actual emitted event name, and 'listenerId' is the receiving listener's ID.`,
    examples: [
      {
        id: "example",
        input: {
          operations: [
            { op: "on", event: "ping", listenerId: "L1" },
            { op: "emit", event: "ping", payload: { time: 100 } }
          ]
        },
        expected: {
          log: [
            { listenerId: "L1", event: "ping", payload: { time: 100 } }
          ]
        }
      }
    ],
    tests: [
      {
        id: "once-and-off",
        input: {
          operations: [
            { op: "once", event: "click", listenerId: "btn-once" },
            { op: "on", event: "click", listenerId: "btn-perm" },
            { op: "emit", event: "click", payload: 1 },
            { op: "emit", event: "click", payload: 2 },
            { op: "off", event: "click", listenerId: "btn-perm" },
            { op: "emit", event: "click", payload: 3 }
          ]
        },
        expected: {
          log: [
            { listenerId: "btn-once", event: "click", payload: 1 },
            { listenerId: "btn-perm", event: "click", payload: 1 },
            { listenerId: "btn-perm", event: "click", payload: 2 }
          ]
        }
      },
      {
        id: "wildcard-matching",
        input: {
          operations: [
            { op: "on", event: "*", listenerId: "global-logger" },
            { op: "on", event: "order.*", listenerId: "order-service" },
            { op: "on", event: "order.paid", listenerId: "receipt-mailer" },
            { op: "emit", event: "order.paid", payload: { orderId: 101 } },
            { op: "emit", event: "user.signup", payload: { userId: 5 } }
          ]
        },
        expected: {
          log: [
            { listenerId: "global-logger", event: "order.paid", payload: { orderId: 101 } },
            { listenerId: "order-service", event: "order.paid", payload: { orderId: 101 } },
            { listenerId: "receipt-mailer", event: "order.paid", payload: { orderId: 101 } },
            { listenerId: "global-logger", event: "user.signup", payload: { userId: 5 } }
          ]
        }
      },
      {
        id: "duplicate-listener-ordering",
        input: {
          operations: [
            { op: "on", event: "msg", listenerId: "A" },
            { op: "on", event: "msg", listenerId: "B" },
            { op: "emit", event: "msg", payload: "hello" }
          ]
        },
        expected: {
          log: [
            { listenerId: "A", event: "msg", payload: "hello" },
            { listenerId: "B", event: "msg", payload: "hello" }
          ]
        }
      }
    ],
    referenceCode: `export function solve(input) {
  const listeners = [];
  const log = [];

  function matches(pattern, event) {
    if (pattern === '*' || pattern === event) return true;
    if (pattern.endsWith('.*')) {
      const prefix = pattern.slice(0, -2);
      return event === prefix || event.startsWith(prefix + '.');
    }
    return false;
  }

  for (const op of input.operations || []) {
    if (op.op === 'on') {
      listeners.push({ event: op.event, listenerId: op.listenerId, once: false });
    } else if (op.op === 'once') {
      listeners.push({ event: op.event, listenerId: op.listenerId, once: true });
    } else if (op.op === 'off') {
      const idx = listeners.findIndex(l => l.event === op.event && l.listenerId === op.listenerId);
      if (idx !== -1) listeners.splice(idx, 1);
    } else if (op.op === 'emit') {
      const toRemove = [];
      for (const l of listeners) {
        if (matches(l.event, op.event)) {
          log.push({ listenerId: l.listenerId, event: op.event, payload: op.payload });
          if (l.once) toRemove.push(l);
        }
      }
      for (const rem of toRemove) {
        const idx = listeners.indexOf(rem);
        if (idx !== -1) listeners.splice(idx, 1);
      }
    }
  }

  return { log };
}`,
    mutants: [
      // Doesn't handle wildcard '*' — fails wildcard-matching test
      `export function solve(input) {
  const listeners = [];
  const log = [];
  for (const op of input.operations || []) {
    if (op.op === 'on') listeners.push({ event: op.event, listenerId: op.listenerId, once: false });
    else if (op.op === 'once') listeners.push({ event: op.event, listenerId: op.listenerId, once: true });
    else if (op.op === 'off') {
      const idx = listeners.findIndex(l => l.event === op.event && l.listenerId === op.listenerId);
      if (idx !== -1) listeners.splice(idx, 1);
    } else if (op.op === 'emit') {
      const toRemove = [];
      for (const l of listeners) {
        if (l.event === op.event) {
          log.push({ listenerId: l.listenerId, event: op.event, payload: op.payload });
          if (l.once) toRemove.push(l);
        }
      }
      for (const rem of toRemove) {
        const idx = listeners.indexOf(rem);
        if (idx !== -1) listeners.splice(idx, 1);
      }
    }
  }
  return { log };
}`
    ]
  })
];

export function getTask(id: string): Task | undefined {
  return coreTasks.find((candidate) => candidate.id === id);
}
