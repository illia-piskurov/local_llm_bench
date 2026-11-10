local BT = {}

-- Execution statuses
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

-- Internal helper for state management in composite nodes
local function createNode(type, ...)
    local node = {}
    node.type = type
    node.__children = {...}
    return node
end

---------------------------------------------------
-- 1. Blackboard Implementation
---------------------------------------------------
BT.Blackboard = {}

function BT.Blackboard.new()
    local bb = {
        data = {},
        watchers = {} -- key -> list of callbacks
    }
    return bb
end

function BT.Blackboard:get(key, default)
    return self.data[key] or default
end

function BT.Blackboard:set(key, value)
    local oldValue = self.data[key]

    if self.data[key] ~= value then
        self.data[key] = value
        -- Trigger watchers if the value actually changed
        if self.watchers[key] then
            for _, callback in ipairs(self.watchers[key] or {}) do
                callback(key, value, oldValue)
            end
        end
    end
end

function BT.Blackboard:watch(key, callback)
    if not self.watchers[key] then
        self.watchers[key] = {}
    end
    table.insert(self.watchers[key], callback)
end

---------------------------------------------------
-- 2. Action Node (Retained for completeness)
---------------------------------------------------
function BT.Action(fn)
    local node = createNode("Action", fn)

    function node:tick(ctx)
        local result = fn(ctx)
        if type(result) == "boolean" then
            return result and BT.SUCCESS or BT.FAILURE
        elseif result == BT.RUNNING then
            return BT.RUNNING
        end
        -- Assumes true or SUCCESS is implicitly handled if fn returns boolean for success case
        return result == true and BT.SUCCESS or BT.FAILURE
    end

    function node:reset()
        -- Actions usually don't have persistent state, but the method exists for interface consistency.
    end

    return node
end

---------------------------------------------------
-- 3. Condition Node (Retained for completeness)
---------------------------------------------------
function BT.Condition(predicate)
    local node = createNode("Condition", predicate)

    function node:tick(ctx)
        local result = predicate(ctx)
        if result == true then
            return BT.SUCCESS
        else
            return BT.FAILURE
        end
    end

    function node:reset()
        -- Conditions usually don't have persistent state.
    end

    return node
end

---------------------------------------------------
-- 4. Sequence Node (Retained for completeness)
---------------------------------------------------
function BT.Sequence(children)
    local node = createNode("Sequence", children)
    node._index = 1 -- Start at the first child

    function node:tick(ctx)
        for i = node._index, #children do
            local child = children[i]

            local result = child:tick(ctx)

            if result == BT.FAILURE then
                return BT.FAILURE
            elseif result == BT.RUNNING then
                -- Store current index to resume later
                node._index = i
                return BT.RUNNING
            end
            -- If SUCCESS, continue to the next child
        end

        -- If loop completes successfully
        return BT.SUCCESS
    end

    function node:reset()
        -- Reset index to start over on next tick
        node._index = 1
    end

    return node
end

---------------------------------------------------
-- 5. Selector Node (Retained for completeness)
---------------------------------------------------
function BT.Selector(children)
    local node = createNode("Selector", children)
    node._index = 1 -- Start at the first child

    function node:tick(ctx)
        for i = node._index, #children do
            local child = children[i]

            local result = child:tick(ctx)

            if result == BT.SUCCESS then
                return BT.SUCCESS
            elseif result == BT.RUNNING then
                -- Store current index to resume later
                node._index = i
                return BT.RUNNING
            end
            -- If FAILURE, continue to the next child (fall back)
        end

        -- If loop completes without finding a success
        return BT.FAILURE
    end

    function node:reset()
        -- Reset index to start over on next tick
        node._index = 1
    end

    return node
end


---------------------------------------------------
-- 6. Decorator: Inverter
---------------------------------------------------
function BT.Inverter(child)
    local node = createNode("Inverter", child)

    function node:tick(ctx)
        local result = child:tick(ctx)

        if result == BT.SUCCESS then
            return BT.FAILURE
        elseif result == BT.FAILURE then
            return BT.SUCCESS
        else -- BT.RUNNING
            return BT.RUNNING
        end
    end

    function node:reset()
        child:reset()
    end

    return node
end


---------------------------------------------------
-- 7. Decorator: Cooldown
---------------------------------------------------
function BT.Cooldown(child, ticks)
    local node = createNode("Cooldown", child)
    node._cooldown_remaining = ticks

    function node:tick(ctx)
        if node._cooldown_remaining > 0 then
            node._cooldown_remaining = node._cooldown_remaining - 1
            if node._cooldown_remaining <= 0 then
                node._cooldown_remaining = 0 -- Ensure it's zero if we hit exactly
            end

            if node._cooldown_remaining > 0 then
                return BT.FAILURE -- Still on cooldown
            else
                -- Cooldown finished, execute child
                return child:tick(ctx)
            end
        else
             -- Should not happen if reset is called correctly, but acts as a safety net
             return child:tick(ctx)
        end
    end

    function node:reset()
        node._cooldown_remaining = ticks
        child:reset()
    end

    return node
end
