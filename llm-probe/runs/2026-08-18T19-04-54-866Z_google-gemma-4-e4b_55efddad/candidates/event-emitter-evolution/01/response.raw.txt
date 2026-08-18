export function solve(input) {
    /**
     * Listener storage structure:
     * Map<Pattern (string), Array<{ id: string, isOnce: boolean, active: boolean }>>
     */
    const listeners = new Map();
    const logEntries = [];

    /**
     * Helper function to get or initialize the listener array for a given pattern.
     * @param {string} eventPattern - The registered pattern (e.g., "user.*", "*").
     * @returns {Array<{ id: string, isOnce: boolean, active: boolean }>}
     */
    const getListeners = (eventPattern) => {
        if (!listeners.has(eventPattern)) {
            listeners.set(eventPattern, []);
        }
        return listeners.get(eventPattern);
    };

    // 1. Process Operations
    for (const operation of input.operations) {
        const { op, event: eventName = "", listenerId } = operation;

        if (!eventName && !listenerId) continue; // Should not happen based on spec, but safety check

        switch (op) {
            case "on":
                // Persistent listener
                getListeners(eventName).push({
                    id: listenerId,
                    isOnce: false,
                    active: true
                });
                break;

            case "once":
                // One-time listener
                getListeners(eventName).push({
                    id: listenerId,
                    isOnce: true,
                    active: true
                });
                break;

            case "off":
                // Unregister specific listener for the given pattern
                if (listeners.has(eventName)) {
                    const existingList = listeners.get(eventName);
                    for (let i = 0; i < existingList.length; i++) {
                        if (existingList[i].id === listenerId) {
                            // Deactivate it permanently upon 'off' command
                            existingList[i].active = false;
                            break;
                        }
                    }
                }
                break;

            case "emit": {
                const actualEvent = eventName;
                const payload = operation.payload;

                // Track which listeners are executed in this cycle to manage 'once' removal correctly
                // We iterate over patterns and then over the listener list, maintaining order.
                const matchedPatterns = [];

                /**
                 * Checks if a registered pattern matches the actual emitted event name.
                 * @param {string} pattern - The registered pattern (e.g., "user.*", "*").
                 * @param {string} emittedEvent - The event being emitted (actual event name).
                 * @returns {boolean} True if it matches.
                 */
                const matches = (pattern, emittedEvent) => {
                    if (pattern === "*") return true; // Global wildcard

                    // Check for prefix wildcard: pattern must end with '.*' and contain a dot separator
                    const prefixMatch = pattern.match(/(.*)\.\*/);
                    if (prefixMatch && pattern.endsWith(".*")) {
                        const requiredPrefix = prefixMatch[1] + ".";
                        return emittedEvent.startsWith(requiredPrefix);
                    }

                    // Exact match
                    return pattern === emittedEvent;
                };

                // Iterate over all patterns registered
                for (const [pattern, listenerList] of listeners) {
                    if (!matches(pattern, actualEvent)) {
                        continue;
                    }

                    // Dispatch event for this matching pattern
                    let currentListeners = [...listenerList]; // Copy to allow safe manipulation/iteration logic if needed

                    for (let i = 0; i < currentListeners.length; i++) {
                        const listener = currentListeners[i];

                        if (!listener.active) continue;

                        // 1. Log Delivery
                        logEntries.push({
                            listenerId: listener.id,
                            event: actualEvent,
                            payload: payload
                        });

                        // 2. Handle 'once' removal
                        if (listener.isOnce) {
                            // Deactivate the listener so it doesn't fire again
                            const index = listeners.get(pattern).findIndex(l => l.id === listener.id);
                            if (index !== -1) {
                                listeners.get(pattern)[index].active = false;
                            }
                        }
                    }
                }
                break;
            }
        }
    }

    return { log: logEntries };
}