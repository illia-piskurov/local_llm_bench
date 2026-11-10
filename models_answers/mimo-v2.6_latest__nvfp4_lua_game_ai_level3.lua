BT = {}

BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

BT.Action = function(fn)
    local node = {
        type = "action",
        fn = fn,
        coroutine = nil,
        wait_ticks = 0,
        status = BT.SUCCESS,
    }

    function node:tick(ctx)
        if self.coroutine == nil or not self.coroutine.isalive then
            self.coroutine = coroutine.create(fn)
        end

        if self.wait_ticks > 0 then
            self.wait_ticks = self.wait_ticks - 1
            return BT.RUNNING
        end

        local result = coroutine.resume(self.coroutine, ctx)
        if result == ("WAIT_TICKS", n) then
            self.wait_ticks = n
            return BT.RUNNING
        end

        return result
    end

    function node:reset()
        self.coroutine = nil
        self.wait_ticks = 0
    end

    return node
end

BT.Condition = function(predicate)
    local node = {
        type = "condition",
        predicate = predicate,
        status = BT.SUCCESS,
    }

    function node:tick(ctx)
        if predicate(ctx) then
            return BT.SUCCESS
        else
            return BT.FAILURE
        end
    end

    function node:reset()
        self.status = BT.SUCCESS
    end

    return node
end

BT.Sequence = function(children)
    local node = {
        type = "sequence",
        children = children,
        index = 1,
        status = BT.SUCCESS,
    }

    function node:tick(ctx)
        local child = children[self.index]
        if not child then
            return BT.SUCCESS
        end

        local result = child:tick(ctx)
        if result == BT.SUCCESS then
            self.index = self.index + 1
            return BT.SUCCESS
        elseif result == BT.RUNNING then
            return BT.RUNNING
        else
            return BT.FAILURE
        end
    end

    function node:reset()
        for _, child in ipairs(self.children) do
            child:reset()
        end
        self.index = 1
    end

    return node
end

BT.Selector = function(children)
    local node = {
        type = "selector",
        children = children,
        index = 1,
        status = BT.SUCCESS,
    }

    function node:tick(ctx)
        local child = children[self.index]
        if not child then
            return BT.SUCCESS
        end

        local result = child:tick(ctx)
        if result == BT.SUCCESS then
            return BT.SUCCESS
        elseif result == BT.RUNNING then
            return BT.RUNNING
        else
            self.index = self.index + 1
            return BT.FAILURE
        end
    end

    function node:reset()
        for _, child in ipairs(self.children) do
            child:reset()
        end
        self.index = 1
    end

    return node
end

BT.Blackboard = {}

BT.Blackboard.new = function()
    local blackboard = {
        data = {},
        watchers = {},
    }

    function blackboard:get(key, default)
        return (self.data[key] == nil) and default or self.data[key]
    end

    function blackboard:set(key, value)
        local old = self.data[key]
        self.data[key] = value
        if old == nil or old ~= value then
            local callbacks = self.watchers[key]
            if callbacks then
                for _, callback in ipairs(callbacks) do
                    callback(key, value, old)
                end
            end
        end
    end

    function blackboard:watch(key, callback)
        if self.watchers[key] == nil then
            self.watchers[key] = {}
        end
        table.insert(self.watchers[key], callback)
    end

    return blackboard
end

BT.Inverter = function(child)
    local node = {
        type = "inverter",
        child = child,
        status = BT.SUCCESS,
    }

    function node:tick()
        local result = self.child:tick()
        if result == BT.SUCCESS then
            return BT.FAILURE
        elseif result == BT.FAILURE then
            return BT.SUCCESS
        else
            return BT.RUNNING
        end
    end

    function node:reset()
        self.child:reset()
    end

    return node
end

BT.Cooldown = function(child, ticks)
    local node = {
        type = "cooldown",
        child = child,
        cooldown = 0,
        status = BT.SUCCESS,
    }

    function node:tick()
        if self.cooldown > 0 then
            self.cooldown = self.cooldown - 1
            return BT.FAILURE
        end

        local result = self.child:tick()
        if result == BT.SUCCESS then
            self.cooldown = ticks
        end

        return result
    end

    function node:reset()
        self.cooldown = 0
        self.child:reset()
    end

    return node
end
