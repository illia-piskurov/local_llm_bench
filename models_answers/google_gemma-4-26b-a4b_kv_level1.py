def run(program: str) -> list[str]:
    """
    Implements an in-memory key-value store with nested transactions.
    """
    # Sentinel object to represent a deleted key in a specific transaction layer
    DELETED = object()
    # layers[0] is the global storage. Subsequent elements are transaction layers.
    layers = [{}]
    output = []

    for line in program.splitlines():
        parts = line.split()
        if not parts:
            continue

        cmd = parts[0]

        if cmd == "SET":
            # Format: SET <key> <value>
            # We use join to allow values to contain spaces if they are provided as single arguments.
            key = parts[1]
            val = " ".join(parts[2:])
            layers[-1][key] = val

        elif cmd == "GET":
            # Format: GET <key>
            key = parts[1]
            found_val = None
            found = False
            # Search from the most recent transaction layer down to the global storage.
            for i in range(len(layers) - 1, -1, -1):
                if key in layers[i]:
                    # If the key is found, check if it was marked as deleted in this layer.
                    if layers[i][key] is not DELETED:
                        found_val = layers[i][key]
                        found = True
                    else:
                        # If it's a DELETED sentinel, the key is considered non-existent in this scope.
                        found = False
                    # Stop searching once the key is found (even if it's a deletion).
                    break
            output.append(str(found_val) if found else "NULL")

        elif cmd == "DELETE":
            # Format: DELETE <key>
            key = parts[1]
            layers[-1][key] = DELETED

        elif cmd == "BEGIN":
            # Format: BEGIN
            layers.append({})

        elif cmd == "COMMIT":
            # Format: COMMIT
            if len(layers) == 1:
                output.append("NO TRANSACTION")
            else:
                # Pop the innermost transaction and merge its changes into the parent layer.
                top_layer = layers.pop()
                for k, v in top_layer.items():
                    layers[-1][k] = v

        elif cmd == "ROLLBACK":
            # Format: ROLLBACK
            if len(layers) == 1:
                output.append("NO TRANSACTION")
            else:
                # Discard the innermost transaction layer.
                layers.pop()

    return output
