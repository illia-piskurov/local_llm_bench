-- Global Behavior Tree namespace
BT = {}

-- Execution statuses
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

-- -----------------------------------------------------------------------------
-- Blackboard Implementation (Shared Memory)
-- -----------------------------------------------------------------------------

--- Creates a new blackboard instance for shared state management.
function BT.Blackboard()
    local self = {
        _data = {},
        _watchers = {} -- Key -> list of callbacks
    }

    return self
end

--- Retrieves the value associated with a key, or default if not found.
-- @param bb The blackboard instance.
-- @param key string The key to retrieve.
-- @param default any The value to return if the key is missing.
function BT.Blackboard:get(key, default)
    return self._data[key] ~= nil and self._data[key] or default
end

--- Stores a value for a given key and triggers watchers if the value changes.
-- @param bb The blackboard instance.
-- @param key string The key to set.
-- @param value any The new value.
function BT.Blackboard:set(key, value)
    local old_value = self._data[key]

    if old_value == value then
        return false -- No change
    end

    self._data[key] = value

    -- Trigger watchers only if the value actually changed
    for _, callback in ipairs(self._watchers[key]) do
        callback(key, value, old_value)
    end

    return true
end

--- Registers a callback function to be executed when a specific key changes.
-- @param bb The blackboard instance.
-- @param key string The key to watch.
-- @param callback function (key, new_value, old_value).
function BT.Blackboard:watch(key, callback)
    if not self._watchers[key] then
        self._watchers[key] = {}
    end
    table.insert(self._watchers[key], callback)
end

-- -----------------------------------------------------------------------------
-- Node Implementations (Existing Nodes - Kept for completeness/context)
-- -----------------------------------------------------------------------------

--- Helper function to check if a status string matches one of the defined constants
local function is_status(s)
    return s == BT.SUCCESS or s == BT.FAILURE or s == BT.RUNNING
end

--- Action Node: Executes a given function (fn).
function BT.Action(fn)
    local self = {
        _fn = fn,
    }

    setmetatable(self, { __index = BT.NodeMethods })

    function self:tick(ctx)
        local result = self._fn(ctx)

        if type(result) == "boolean" then
            return result and BT.SUCCESS or BT.FAILURE
        elseif type(result) == "string" and is_status(result) then
            return result
        else
            -- Handle explicit true/false returns, otherwise default to failure
            return (result == true or result == "SUCCESS") and BT.SUCCESS or BT.FAILURE
        end
    end

    function self:reset() end

    return self
end


--- Condition Node: Checks a predicate function.
function BT.Condition(predicate)
    local self = {
        _predicate = predicate,
    }

    setmetatable(self, { __index = BT.NodeMethods })

    function self:tick(ctx)
        return self._predicate(ctx) and BT.SUCCESS or BT.FAILURE
    end

    function self:reset() end

    return self
end


-- -----------------------------------------------------------------------------
-- Composite Node Base Methods (Shared logic for state management)
BT.NodeMethods = {}

-- Sequence implementation remains the same...
function BT.Sequence(children)
    local self = {
        _children = children,
        _current_child_index = 1,
    }

    setmetatable(self, { __index = BT.NodeMethods })

    function self:tick(ctx)
        local children = self._children
        local index = self._current_child_index

        if not children or #children == 0 then return BT.FAILURE end

        -- Resetting logic check (should only happen if parent calls reset, but safe guard here)
        if index < 1 then
             self._current_child_index = 1
             index = 1
        end

        local child = children[index]
        local status = child:tick(ctx)

        if status == BT.FAILURE then
            return BT.FAILURE
        elseif status == BT.RUNNING then
            return BT.RUNNING
        else -- SUCCESS
            -- Check if this was the last child
            if index == #children then
                self._current_child_index = 1
                return BT.SUCCESS
            else
                -- Successful, but more children remain. Advance pointer and signal RUNNING state maintenance.
                self._current_child_index = index + 1
                return BT.RUNNING
            end
        end
    end

    function self:reset()
        self._current_child_index = 1
    end

    return self
end


-- Selector implementation remains the same...
function BT.Selector(children)
    local self = {
        _children = children,
        _current_child_index = 1,
    }

    setmetatable(self, { __index = BT.NodeMethods })

    function self:tick(ctx)
        local children = self._children
        local index = self._current_child_index

        if not children or #children == 0 then return BT.FAILURE end

        if index < 1 then
             self._current_child_index = 1
             index = 1
        end

        local child = children[index]
        local status = child:tick(ctx)

        if status == BT.SUCCESS then
            return BT.SUCCESS
        elseif status == BT.RUNNING then
            return BT.RUNNING
        else -- FAILURE
            -- Check if this was the last child
            if index == #children then
                self._current_child_index = 1
                return BT.FAILURE
            else
                -- Failed, but more children remain. Keep position and signal RUNNING state maintenance.
                return BT.RUNNING
            end
        end
    end

    function self:reset()
        self._current_child_index = 1
    end

    return self
end


-- -----------------------------------------------------------------------------
-- Decorator Nodes (Single Child Wrappers)
-- -----------------------------------------------------------------------------

--- Inverter Node: Flips the result of its child.
function BT.Inverter(child)
    local self = {
        _child = child,
    }

    setmetatable(self, { __index = BT.NodeMethods })

    function self:tick(ctx)
        local status = self._child:tick(ctx)

        if status == BT.SUCCESS then
            return BT.FAILURE -- Invert Success to Failure
        elseif status == BT.FAILURE then
            return BT.SUCCESS -- Invert Failure to Success
        else -- RUNNING remains RUNNING
            return BT.RUNNING
        end
    end

    function self:reset()
        self._child:reset()
    end

    return self
end


--- Cooldown Node: Forces failure for a specified number of ticks after success.
function BT.Cooldown(child, ticks)
    local self = {
        _child = child,
        _cooldown_ticks = ticks or 1,
        _remaining_ticks = 0,
    }

    setmetatable(self, { __index = BT.NodeMethods })

    function self:tick(ctx)
        if self._remaining_ticks > 0 then
            -- Cooldown active: Fail immediately and decrement counter
            self._remaining_ticks -= 1
            return BT.FAILURE
        else
            -- Cooldown expired or never started: Execute child normally
            local status = self._child:tick(ctx)

            if status == BT.SUCCESS then
                -- Success triggers cooldown
                self._remaining_ticks = self._cooldown_ticks
                return BT.RUNNING -- Signal that the node is now in a waiting/cooling state
            else
                return status
            end
        end
    end

    function self:reset()
        self._remaining_ticks = 0
        self._child:reset()
    end

    return self
end


-- Expose all nodes under the global table (including Blackboard)
BT.Blackboard = BT.Blackboard
BT.Action = function(fn) return BT.Action(fn) end
BT.Condition = function(predicate) return BT.Condition(predicate) end
BT.Sequence = function(children) return BT.Sequence(children) end
BT.Selector = function(children) return BT.Selector(children) end

-- Decorators
BT.Inverter = function(child) return BT.Inverter(child) end
BT.Cooldown = function(child, ticks) return BT.Cooldown(child, ticks) end
