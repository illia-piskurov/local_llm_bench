BT = {}
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

BT.Blackboard = {}
BT.Blackboard.new = function()
    local bb = {}
    bb.data = {}
    return bb
end
BT.Blackboard.get = function(bb, key, default)
    if bb.data[key] then
        return bb.data[key]
    else
        return default
    end
end
BT.Blackboard.set = function(bb, key, value)
    bb.data[key] = value
    for k, v in pairs(bb.watchers) do
        if k == key then
            v(key, value, bb.data[key])
        end
    end
end
BT.Blackboard.watch = function(bb, key, callback)
    bb.watchers[key] = callback
end

BT.Inverter = function(child)
    local node = {}
    node.child = child
    node.status = BT.RUNNING

    node.tick = function(ctx)
        node.status = node.child:tick(ctx)
        if node.status == BT.SUCCESS or node.status == BT.FAILURE then
            return BT.FAILURE
        elseif node.status == BT.RUNNING then
            return BT.RUNNING
        end
    end

    node.reset = function()
        node.child:reset()
    end

    return node
end

BT.Cooldown = function(child, ticks)
    local node = {}
    node.child = child
    node.ticks = ticks
    node.cooldownTick = 0
    node.status = BT.RUNNING

    node.tick = function(ctx)
        node.cooldownTick = node.cooldownTick + 1
        if node.cooldownTick > node.ticks then
            node.status = node.child:tick(ctx)
            if node.status == BT.SUCCESS then
                node.cooldownTick = 0
            elseif node.status == BT.RUNNING then
                return BT.RUNNING
            end
        end
    end

    node.reset = function()
        node.cooldownTick = 0
        node.child:reset()
    end

    return node
end
