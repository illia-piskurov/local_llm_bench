function BT.AsyncAction(coroutine_fn)
    local co = nil
    local waitTicks = 0
    local tickCount = 0
    local finished = false
    local function tick(ctx)
        if not finished then
            if co and coroutine.status(co) ~= "dead" then
                if waitTicks > 0 then
                    waitTicks = waitTicks - 1
                    return BT.RUNNING
                else
                    co = coroutine.resume(co, ctx)
                    if co == "yield" and co.args[1] == "WAIT_TICKS" then
                        waitTicks = tonumber(co.args[2])
                        return BT.RUNNING
                    end
                end
                finished = true
            end
            if finished and coroutine.status(co) == "dead" then
                return co
            end
        end
        return finished and coroutine.status(co) == "dead" and co or BT.FAILURE
    end
    function tick.reset()
        if co then
            coroutine.close(co)
        end
        co = nil
        waitTicks = 0
        tickCount = 0
    end
    return tick
end

function BT.Sequence(children)
    local childrenCount = #children
    local index = 1
    local cooldownTicks = 0
    local lastResult = BT.FAILURE
    local childrenToReset = {}
    local function tick(ctx)
        if index > childrenCount then
            return lastResult == BT.FAILURE and cooldownTicks > 0 and cooldownTicks > 1 or lastResult == BT.SUCCESS
        end
        local child = children[index]
        local result = child(ctx)
        if result == BT.FAILURE then
            return result
        elseif result == BT.RUNNING then
            index = index + 1
            return result
        else
            lastResult = result
            index = index + 1
            if result == BT.SUCCESS then
                cooldownTicks = cooldownTicks + 1
            else
                cooldownTicks = 0
            end
            for _, child in ipairs(children) do
                table.insert(childrenToReset, child)
            end
            return result
        end
    end
    function tick.reset()
        for _, child in ipairs(children) do
            child.reset()
        end
        index = 1
        cooldownTicks = 0
        lastResult = BT.FAILURE
        childrenToReset = {}
    end
    return tick
end

function BT.Selector(children)
    local childrenCount = #children
    local index = 1
    local cooldownTicks = 0
    local lastResult = BT.FAILURE
    local childrenToReset = {}
    local function tick(ctx)
        if index > childrenCount then
            return lastResult == BT.FAILURE and cooldownTicks > 0 and cooldownTicks > 1 or lastResult == BT.SUCCESS
        end
        local child = children[index]
        local result = child(ctx)
        if result == BT.SUCCESS then
            return result
        elseif result == BT.RUNNING then
            index = index + 1
            return result
        end
    end
    function tick.reset()
        for _, child in ipairs(children) do
            child.reset()
        end
        index = 1
        cooldownTicks = 0
        lastResult = BT.FAILURE
        childrenToReset = {}
    end
    return tick
end
