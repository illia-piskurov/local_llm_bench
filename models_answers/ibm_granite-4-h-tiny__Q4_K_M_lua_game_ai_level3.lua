local BT = {}

-- Execution statuses
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

-- Action node
function BT.Action(coroutineFn)
    return {
        tick = function(ctx)
            if not self.coroutine then
                self.coroutine = coroutine.create(coroutineFn)
            end

            if self.waitTicks > 0 then
                self.waitTicks = self.waitTicks - 1
                return BT.RUNNING
            end

            local ok, result = coroutine.resume(self.coroutine, ctx)

            if not ok then
                self.coroutine = nil
                return result or BT.FAILURE
            elseif self.waitTicks > 0 then
                self.waitTicks = self.waitTicks - 1
                return BT.RUNNING
            else
                return result or BT.SUCCESS
            end
        end,
        reset = function()
            self.coroutine = nil
            self.waitTicks = 0
        end
    }
end

-- Asynchronous action with wait ticks
function BT.AsyncAction(coroutineFn)
    local node = BT.Action(coroutineFn)
    return {
        setWaitTicks = function(n)
            node.waitTicks = n
        end,
        reset = function()
            node.reset()
        end
    }
end

-- Sequence node (logical AND) with cascading resets
function BT.Sequence(children)
    local index = 1
    return {
        tick = function(ctx)
            while true do
                if index > #children then
                    return BT.SUCCESS
                elseif index < 1 then
                    error("Invalid sequence index")
                end

                local result = children[index]:tick(ctx)

                if result == BT.FAILURE or result == BT.RUNNING then
                    for i = index, #children do
                        children[i]:reset()
                    end
                    return result or BT.FAILURE
                elseif result == BT.SUCCESS then
                    index = index + 1
                end
            end
        end,
        reset = function()
            index = 1
            for _, child in ipairs(children) do
                child:reset()
            end
        end
    }
end

-- Selector node (logical OR / Fallback) with cascading resets
function BT.Selector(children)
    local index = 1
    return {
        tick = function(ctx)
            while true do
                if index > #children then
                    return BT.FAILURE
                elseif index < 1 then
                    error("Invalid selector index")
                end

                local result = children[index]:tick(ctx)

                if result == BT.SUCCESS or result == BT.RUNNING then
                    return result or BT.SUCCESS
                elseif result == BT.FAILURE then
                    index = index + 1
                end
            end
        end,
        reset = function()
            index = 1
            for _, child in ipairs(children) do
                child:reset()
            end
        end
    }
end

-- Blackboard for shared memory
function BT.Blackboard.new()
    local bb = {
        data = {},
        watchers = {}
    }

    function bb:get(key, default)
        return self.data[key] or default
    end

    function bb:set(key, value)
        if self.data[key] ~= value then
            self.data[key] = value
            for _, callback in ipairs(self.watchers[key] or {}) do
                callback(key, value, self.data[key])
            end
        end
    end

    function bb:watch(key, callback)
        if not self.watchers[key] then
            self.watchers[key] = {}
        end
        table.insert(self.watchers[key], callback)
    end

    return bb
end

-- Inverter decorator (single-child node) with cascading resets
function BT.Inverter(child)
    local invertedChild = {
        tick = function(ctx)
            local result = child:tick(ctx)
            if result == BT.SUCCESS then
                return BT.FAILURE
            elseif result == BT.FAILURE then
                return BT.SUCCESS
            else
                return result
            end
        end,
        reset = function()
            child:reset()
        end
    }
    return invertedChild
end

-- Cooldown decorator (single-child node) with cascading resets
function BT.Cooldown(child, ticks)
    local cooldownTicks = 0
    local lastSuccessTime = nil

    local cooledChild = {
        tick = function(ctx)
            if cooldownTicks > 0 then
                cooldownTicks = cooldownTicks - 1
                return BT.FAILURE
            end
            
            local result = child:tick(ctx)
            if result == BT.SUCCESS then
                lastSuccessTime = os.clock()
                cooldownTicks = ticks
            elseif result == BT.RUNNING then
                return BT.RUNNING
            end

            return result
        end,
        reset = function()
            child:reset()
            cooldownTicks = 0
            lastSuccessTime = nil
        end
    }
    return cooledChild
end

return BT
