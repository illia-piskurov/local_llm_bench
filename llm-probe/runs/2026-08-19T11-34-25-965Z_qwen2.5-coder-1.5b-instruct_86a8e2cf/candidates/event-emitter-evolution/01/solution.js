export function solve(input) {
  const events = {};
  const log = [];

  for (const op of input.operations) {
    switch (op.op) {
      case 'on':
        registerListener(op.event, op.listenerId);
        break;
      case 'once':
        registerOnceListener(op.event, op.listenerId);
        break;
      case 'off':
        removeListener(op.event, op.listenerId);
        break;
      case 'emit':
        emitEvent(op.event, op.payload);
        break;
    }
  }

  return { log };

  function registerListener(event, listenerId) {
    if (!events[event]) events[event] = [];
    events[event].push(listenerId);
  }

  function registerOnceListener(event, listenerId) {
    const onOffCallback = (payload) => {
      removeListener(event, listenerId);
      return payload;
    };
    registerListener(event, onOffCallback);
  }

  function removeListener(event, listenerId) {
    if (!events[event]) return;

    events[event] = events[event].filter(id => id !== listenerId);

    const wildcardListeners = [];
    for (const [k, v] of Object.entries(events)) {
      if (!k.startsWith('*')) continue;
      wildcardListeners.push(...v.filter(id => id === listenerId));
    }

    for (const listenerId of wildcardListeners) {
      removeListener(k.slice(1), listenerId);
    }
  }

  function emitEvent(event, payload) {
    if (!events[event]) return;

    const results = [];
    for (const listenerId of events[event]) {
      const result = listeners[listenerId](payload);
      results.push({ listenerId, event, payload: result });
    }

    log.push(...results);

    return results;
  }
}