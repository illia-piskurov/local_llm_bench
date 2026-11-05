BT = {}

BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

BT.Action = function(fn)
    local node = {}
    node.fn = fn
    node.status = BT.RUNNING

    node.tick = function(ctx)
        node.status = node.fn(ctx)
        if node.status == BT.SUCCESS or node.status == BT.FAILURE or node.status == BT.RUNNING then
            return node.status
        end
    end

    node.reset = function()
        node.status = BT.RUNNING
    end

    return node
end

BT.Condition = function(predicate)
    local node = {}
    node.predicate = predicate
    node.status = BT.RUNNING

    node.tick = function(ctx)
        node.status = predicate(ctx)
        if node.status == BT.SUCCESS or node.status == BT.FAILURE then
            return node.status
        end
    end

    node.reset = function()
        node.status = BT.RUNNING
    end

    return node
end

BT.Sequence = function(children)
    local node = {}
    node.children = children
    node.currentChild = 1
    node.status = BT.RUNNING

    node.tick = function(ctx)
        while node.currentChild <= #node.children do
            local childStatus = node.children[node.currentChild]:tick(ctx)
            if childStatus == BT.FAILURE or childStatus == BT.RUNNING then
                return childStatus
            end
            node.currentChild = node.currentChild + 1
        end
        return BT.SUCCESS
    end

    node.reset = function()
        node.currentChild = 1
    end

    return node
end

BT.Selector = function(children)
    local node = {}
    node.children = children
    node.currentChild = 1
    node.status = BT.RUNNING

    node.tick = function(ctx)
        while node.currentChild <= #node.children do
            local childStatus = node.children[node.currentChild]:tick(ctx)
            if childStatus == BT.SUCCESS or childStatus == BT.FAILURE then
                return childStatus
            end
            node.currentChild = node.currentChild + 1
        end
        return BT.FAILURE
    end

    node.reset = function()
        node.currentChild = 1
    end

    return node
end
