local BT = require("path.to.behavior_tree") -- Adjust path as needed

-- Shared blackboard storage
local bbMemory = {}

-- Blackboard functions
function BB_Get(key, default)
    local value = bbMemory[key]
    return (value ~= nil and value) or default
end

function BB_Set(key, value)
    if bbMemory[key] == value then return end -- No change

    bbMemory[key] = value

    local watchers = bbMemory.watchers and bbMemory.watchers[key]
    if watchers then
        for _,watcher in ipairs(watchers) do
            watcher(key, value, bbMemory[key])
        end
    end
end

function BB_Watch(key, callback)
    local watchers = bbMemory.watchers and bbMemory.watchers[key] or {}
    table.insert(watchers, callback)

    bbMemory.watchers = bbMemory.watchers or {}
    bbMemory.watchers[key] = watchers
end

-- Decorators
local function Inverter(child)
    return {
        tick = function(self, ctx)
            local result = child:tick(ctx)
            if result == BT.SUCCESS then
                return BT.FAILURE
            elseif result == BT.FAILURE then
                return BT.SUCCESS
            else -- Assume RUNNING is passed through unchanged
                return result
            end
        end,
        reset = function(self)
            self.child:reset()
        end,
        child = child
    }
end

local function Cooldown(child, ticks)
    local cooldownTicks = 0
    local lastSuccessTime = nil

    return {
        tick = function(self, ctx)
            if cooldownTicks > 0 then
                cooldownTicks = cooldownTicks - 1
                return BT.FAILURE
            end

            local result = child:tick(ctx)

            if result == BT.SUCCESS then
                cooldownTicks = ticks
                lastSuccessTime = os.clock()
            elseif result == BT.RUNNING then
                return result
            end

            cooldownTicks = 0
            lastSuccessTime = nil

            return result
        end,
        reset = function(self)
            self.child:reset()
            cooldownTicks = 0
            lastSuccessTime = nil
        end,
        child = child
    }
end

-- Register blackboard functions on BT for global access
BT.Blackboard = {
    new = function() return { watchers = {}, set = BB_Set, get = BB_Get } end,
    watch = BB_Watch
}

return BT
