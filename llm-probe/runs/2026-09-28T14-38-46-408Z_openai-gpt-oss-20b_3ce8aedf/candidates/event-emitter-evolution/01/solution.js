export function solve(input) {
  const ops = input.operations;
  // Maintain a list of registrations in order
  const listeners = []; // { event, id, once }
  const log = [];

  for (const op of ops) {
    if (op.op === 'on' || op.op === 'once') {
      listeners.push({ event: op.event, id: op.listenerId, once: op.op === 'once' });
    } else if (op.op === 'off') {
      // remove matching registration(s)
      for (let i = listeners.length - 1; i >= 0; i--) {
        const l = listeners[i];
        if (l.event === op.event && l.id === op.listenerId) {
          listeners.splice(i, 1);
        }
      }
    } else if (op.op === 'emit') {
      const eventName = op.event;
      const payload = op.payload;

      // Determine matching listeners in registration order
      for (let i = 0; i < listeners.length; i++) {
        const l = listeners[i];
        let match = false;
        if (l.event === '*') {
          match = true;
        } else if (l.event.endsWith('.*')) {
          const prefix = l.event.slice(0, -2);
          if (eventName.startsWith(prefix + '.')) {
            match = true;
          }
        } else if (l.event === eventName) {
          match = true;
        }

        if (match) {
          log.push({ listenerId: l.id, event: eventName, payload });

          if (l.once) {
            listeners.splice(i, 1);
            i--; // adjust index after removal
          }
        }
      }
    }
  }

  return { log };
}