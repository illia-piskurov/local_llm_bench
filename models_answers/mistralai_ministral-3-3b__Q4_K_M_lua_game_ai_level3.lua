local BT = {}

-- Execution statuses (unchanged)
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

-- Blackboard implementation (unchanged)
BT.Blackboard = {}
function BT.Blackboard.new()
    local self = setmetatable({}, { __index = BT.Blackboard })
    local data = {}
    local watchers = {}

    function self:get(key, default)
        return data[key] or default
    end

    function self:set(key, value)
        local old_value = data[key]
        data[key] = value
        if old_value ~= value then
            for _, callback in ipairs(watchers[key]) do
                callback(key, value, old_value)
            end
        end
    end

    function self:watch(key, callback)
        if not watchers[key] then watchers[key] = {} end
        table.insert(watchers[key], callback)
    end

    return setmetatable({}, { __index = self })
end

-- Decorators (unchanged)
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

    return node
end

function BT.Cooldown(child, ticks)
    local node = new_node()
    local cooldown_ticks = 0
    local last_success_time = 0

    function node:tick(ctx)
        if cooldown_ticks > 0 then
            cooldown_ticks = max(0, cooldown_ticks - 1)
            return BT.FAILURE
        end

        local result = child:tick(ctx)

        if result == BT.SUCCESS then
            last_success_time = tick()
            cooldown_ticks = ticks
            return BT.RUNNING
        else
            return result
        end
    end

    function node:reset()
        child:reset()
        cooldown_ticks = 0
    end

    return node
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

    local function tick(ctx)
        local result = fn(ctx)
        if result == true then return BT.SUCCESS end
        if result == false then return BT.FAILURE end
        if result == BT.SUCCESS then return BT.SUCCESS end
        if result == BT.FAILURE then return BT.FAILURE end
        return BT.RUNNING
    end

    function node:tick(ctx)
        return tick(ctx)
    end

    function node:reset()
        -- No state to reset for Action nodes
    end

    return node
end

-- Condition Node (unchanged)
function BT.Condition(predicate)
    local node = new_node()

    local function tick(ctx)
        if predicate(ctx) then return BT.SUCCESS else return BT.FAILURE end
    end

    function node:tick(ctx)
        return tick(ctx)
    end

    function node:reset()
        -- No state to reset for Condition nodes
    end

    return node
end

-- Sequence Node (AND, unchanged with cascading reset)
function BT.Sequence(children)
    local node = new_node()

    local current_child_index = 1
    function node:tick(ctx)
        if current_child_index > #children then return BT.FAILURE end
        local child = children[current_child_index]
        local result = child:tick(ctx)

        if result == BT.RUNNING then
            current_child_index = current_child_index + 1
            return BT.RUNNING
        elseif result == BT.SUCCESS then
            current_child_index = current_child_index + 1
            return BT.SUCCESS
        else -- FAILURE
            return BT.FAILURE
        end
    end

    function node:reset()
        for _, child in ipairs(children) do child:reset() end
        current_child_index = 1
    end

    return node
end

-- Selector Node (OR / Fallback, unchanged with cascading reset)
function BT.Selector(children)
    local node = new_node()

    local current_child_index = 1
    function node:tick(ctx)
        if current_child_index > #children then return BT.FAILURE end
        local child = children[current_child_index]
        local result = child:tick(ctx)

        if result == BT.RUNNING then
            current_child_index = current_child_index + 1
            return BT.RUNNING
        elseif result == BT.SUCCESS then
            return BT.SUCCESS
        else -- FAILURE
            current_child_index = current_child_index + 1
            return BT.FAILURE
        end
    end

    function node:reset()
        for _, child in ipairs(children) do child:reset() end
        current_child_index = 1
    end

    return node
end

-- Async Action Node (new)
function BT.AsyncAction(coroutine_fn)
    local node = new_node()

    local co, wait_ticks = nil, 0
    function node:tick(ctx)
        if not co then
            co = coroutine.create(function()
                local result = coroutine_fn(ctx)
                if type(result) == "table" and result[1] == "WAIT_TICKS" then
                    wait_ticks = result[2]
                    return BT.RUNNING
                end
                return result
            end)
        end

        if wait_ticks > 0 then
            wait_ticks = max(0, wait_ticks - 1)
            coroutine.resume(co)
            return BT.RUNNING
        else
            local status, result = coroutine.resume(co)
            if status == "normal" then
                return result
            end
        end

        return BT.FAILURE
    end

    function node:reset()
        co = nil
        wait_ticks = 0
    end

    return node
end
