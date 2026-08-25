export function solve(input) {
  const listeners = new Map();
  const wildcardListeners = [];

  function registerListener(op, event, listenerId) {
    if (op === 'on') {
      if (listeners.has(event)) {
        listeners.get(event).add(listenerId);
      } else {
        listeners.set(event, new Set([listenerId]));
      }
    } else if (op === 'once') {
      const listenerSet = new Set();
      listenerSet.add(listenerId);
      wildcardListeners.push({ event, listener: () => listenerSet.delete(listenerId) });
    }
  }

  function unregisterListener(op, event, listenerId) {
    if (listeners.has(event)) {
      listeners.get(event).delete(listenerId);
    }
  }

  function emitEvent(event, payload) {
    const log = [];
    for (const [wildcard, listener] of wildcardListeners) {
      if (event.startsWith(wildcard)) {
        log.push({ listenerId: 'wildcard', event, payload });
        listener();
      }
    }
    if (listeners.has(event)) {
      listeners.get(event).forEach(listenerId => {
        log.push({ listenerId, event, payload });
      });
    }
    return { log };
  }

  input.operations.forEach(op => {
    registerListener(op.op, op.event, op.listenerId);
  });

  const result = emitEvent(input.operations[input.operations.length - 1].event, input.operations[input.operations.length - 1].payload);

  for (const [op, event, listenerId] of input.operations.slice(0, -1)) {
    unregisterListener(op.op, event, listenerId);
  }

  return result;
}