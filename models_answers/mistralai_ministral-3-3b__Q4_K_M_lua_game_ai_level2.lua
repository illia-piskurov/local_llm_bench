local BT = {}

-- Execution statuses (unchanged)
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

-- Blackboard implementation
BT.Blackboard = {}
function BT.Blackboard.new()
    local self = setmetatable({}, { __index = BT.Blackboard })
    self._data = {}
    self._watchers = {}
    return self
end

function BT.Blackboard:get(self, key, default)
    return self._data[key] or default
end

function BT.Blackboard:set(self, key, value)
    local old_value = self._data[key]
    if old_value ~= value then
        self._data[key] = value
        for _, callback in ipairs(self._watchers[key]) do
            callback(key, value, old_value)
        end
    end
end

function BT.Blackboard:watch(self, key, callback)
    if not self._watchers[key] then
        self._watchers[key] = {}
    end
    table.insert(self._watchers[key], callback)
end

-- Decorators
function BT.Inverter(child)
    local node = new_node()
    function node:tick(ctx)
        local result = child:tick(ctx)
        if result == BT.SUCCESS then return BT.FAILURE end
        if result == BT.FAILURE then return BT.SUCCESS end
        return result
    end

    function node:reset()
        child:reset()
    end

    return setmetatable(node, { __index = BT })
end

function BT.Cooldown(child, ticks)
    local node = new_node()
    local cooldown = 0

    function node:tick(ctx)
        if cooldown > 0 then
            cooldown = max(0, cooldown - 1)
            return BT.FAILURE
        end

        local result = child:tick(ctx)
        if result == BT.SUCCESS then
            cooldown = ticks
            return BT.RUNNING
        else
            return result
        end
    end

    function node:reset()
        cooldown = 0
        child:reset()
    end

    return setmetatable(node, { __index = BT })
end

-- Base Node class (unchanged)
local function new_node()
    return setmetatable({}, {
        __index = function(self, key)
            error("Attempt to access non-existent method: " .. key)
        end
    })
end

-- Action Node (unchanged)
function BT.Action(fn)
    local node = new_node()

    function node:tick(ctx)
        local result = fn(ctx)
        if result == true then return BT.SUCCESS end
        if result == false then return BT.FAILURE end
        if result == BT.SUCCESS then return BT.SUCCESS end
        if result == BT.FAILURE then return BT.FAILURE end
        return BT.RUNNING
    end

    function node:reset()
        -- No state to reset for Action nodes
    end

    return setmetatable(node, { __index = BT })
end

-- Condition Node (unchanged)
function BT.Condition(predicate)
    local node = new_node()

    function node:tick(ctx)
        if predicate(ctx) then return BT.SUCCESS else return BT.FAILURE end
    end

    function node:reset()
        -- No state to reset for Condition nodes
    end

    return setmetatable(node, { __index = BT })
end

-- Sequence Node (AND) - unchanged
function BT.Sequence(children)
    local node = new_node()
    local children = children or {}
    local current_index = 1

    function node:tick(ctx)
        if current_index > #children then
            return BT.SUCCESS
        end

        local child = children[current_index]
        local result = child:tick(ctx)

        if result == BT.FAILURE then
            return BT.FAILURE
        elseif result == BT.RUNNING then
            current_index = current_index + 1
            return BT.RUNNING
        else
            current_index = current_index + 1
            return BT.SUCCESS
        end
    end

    function node:reset()
        current_index = 1
    end

    return setmetatable(node, { __index = BT })
end

-- Selector Node (OR) - unchanged
function BT.Selector(children)
    local node = new_node()
    local children = children or {}
    local current_index = 1

    function node:tick(ctx)
        if current_index > #children then
            return BT.FAILURE
        end

        local child = children[current_index]
        local result = child:tick(ctx)

        if result == BT.SUCCESS then
            return BT.SUCCESS
        elseif result == BT.RUNNING then
            current_index = current_index + 1
            return BT.RUNNING
        else
            current_index = current_index + 1
            return BT.FAILURE
        end
    end

    function node:reset()
        current_index = 1
    end

    return setmetatable(node, { __index = BT })
end
