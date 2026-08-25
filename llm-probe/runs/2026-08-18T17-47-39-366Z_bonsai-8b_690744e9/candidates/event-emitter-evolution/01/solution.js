export function solve(input) {
  const eventEmitters = new Map();

  const log = [];

  for (const operation of input.operations) {
    const { op, event, listenerId } = operation;

    if (op === "on") {
      // Register a persistent listener
      if (!eventEmitters.has(event)) {
        eventEmitters.set(event, []);
      }
      eventEmitters.get(event).push(listenerId);
    } else if (op === "once") {
      // Register a one-time listener
      if (!eventEmitters.has(event)) {
        eventEmitters.set(event, []);
      }
      eventEmitters.get(event).push({ op: "once", listenerId });
    } else if (op === "off") {
      // Unregister a specific listener
      const listeners = eventEmitters.get(event);
      if (listeners && listeners.includes(listenerId)) {
        listeners.splice(listeners.indexOf(listenerId), 1);
      }
    } else if (op === "emit") {
      // Emit an event and trigger listeners
      const listeners = eventEmitters.get(event);
      if (!listeners) continue;

      for (const listener of listeners) {
        if (listener.op === "once") {
          log.push({ listenerId: listener.listenerId, event: event, payload: listener.payload });
          // One-time listener is automatically removed after first invocation
          const index = listeners.indexOf(listener);
          listeners.splice(index, 1);
        }
      }
    }
  }

  return { log };
}