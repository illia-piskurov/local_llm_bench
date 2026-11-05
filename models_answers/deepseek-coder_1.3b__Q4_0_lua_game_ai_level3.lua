BT = {}
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

BT.AsyncAction = function(coroutine_fn)
    local node = {}
    node.coroutine = nil
    node.tick = function(ctx)
        if node.coroutine then
            coroutine.resume(node.coroutine, ctx)
        else
            node.coroutine = coroutine.create(coroutine_fn)
            coroutine.resume(node.coroutine, ctx)
        end
        return BT.RUNNING
    end
    node.reset = function()
        if node.coroutine then
            coroutine.resume(node.coroutine, true)
            node.coroutine = nil
        end
    end
    return node
end

BT.Sequence = function(children)
    local node = {}
    node.children = children
    node.tick = function(ctx)
        for _, child in ipairs(node.children) do
            ctx = child:tick(ctx)
            if ctx == BT.FAILURE then
                return BT.FAILURE
            elseif ctx == BT.SUCCESS then
                ctx = child:reset()
            end
        end
        return ctx
    end
    node.reset = function()
        for _, child in ipairs(node.children) do
            child:reset()
        end
    end
    return node
end

BT.Selector = function(children)
    local node = {}
    node.children = children
    node.tick = function(ctx)
        for _, child in ipairs(node.children) do
            ctx = child:tick(ctx)
            if ctx == BT.SUCCESS or ctx == BT.FAILURE then
                return ctx
            end
        end
        return BT.FAILURE
    end
    node.reset = function()
        for _, child in ipairs(node.children) do
            child:reset()
        end
    end
    return node
end
