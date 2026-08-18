export function solve(input) {
  const listeners = {};

  for (const { op, event, listenerId, payload } of input.operations) {
    if (!listeners[event]) listeners[event] = [];

    switch (op) {
      case "on":
        listeners[event].push({ id: listenerId });
        break;
      case "once":
        listeners[event].push({ id: listenerId, once: true });
        break;
      case "off":
        listeners[event] = listeners[event].filter((l) => l.id !== listenerId);
        break;
      case "emit":
        for (const { id } of listeners[event]) {
          if ((op === "emit" && id.id === event) || (id.once && op === "emit" && id.id.startsWith(event + "."))) {
            console.log({ log: [{ listenerId: id, event, payload }] });
          }
        }
        break;
    }
  }

  return { log: [] };
}