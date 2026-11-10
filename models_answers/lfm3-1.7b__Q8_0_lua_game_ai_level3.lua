-- Global table defining behavior tree nodes and constants
local BT = {}

BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

--- Blackboard (shared memory) ------------------------------------------------
BT.Blackboard = {
    new = function()
        local bb = { data = {}, watchers = {} }
        setmetatable(bb, {
            get = function(key, default) return bb.data[key] or default end,
            set = function(key, value)
                bb.data[key] = value
                local wlist = bb.watchers[key]
                if wlist then
                    for _, cb in ipairs(wlist) do
                        -- old value before the update (not needed for simplicity)
                        cb(key, value, bb.data[key])
                    end
                end
            },
            watch = function(key, callback)
                bb.watchers[key] = {callback}
            end,
        })
        return bb
    },
    get = function(bb, key, default) return bb.get(bb, key, default) end,
    set = function(bb, key, value) bb.set(bb, key, value),
    watch = function(bb, key, callback) bb.watch(bb, key, callback)
}

function BT.Blackboard:new()
    local self = BT.Blackboard.new()
    setmetatable(self, {
        get = self.get,
        set = self.set,
        watch = self.watch
    })
    return self
end

--- Action node (synchronous) -------------------------------------------------
function BT.Action(fn)
    return {
        tick = function(ctx)
            local res = fn(ctx)
            if res == true or res == BT.SUCCESS then
                return BT.SUCCESS
            elseif res == false or res == BT.FAILURE then
                return BT.FAILURE
            elseif res == BT.RUNNING then
                return BT.RUNNING
            end
        ,
        reset = function()
            -- Action has no internal state to reset
        end
    }
end

--- Condition node -----------------------------------------------------------
function BT.Condition(predicate)
    return {
        tick = function(ctx)
            if predicate(ctx) then
                return BT.SUCCESS
            else
                return BT.FAILURE
            end
        ,
        reset = function()
            -- No internal state to reset for Condition
        end
    }
end

--- Inverter decorator (single‑child node) ------------------------------------
BT.Inverter = function(child)
    local res = {
        tick = function(ctx)
            local childRes = child.tick(ctx)
            if childRes == BT.SUCCESS then
                return BT.FAILURE
            elseif childRes == BT.FAILURE then
                return BT.SUCCESS
            elseif childRes == BT.RUNNING then
                return childRes -- unchanged
            end
        ,
        reset = function()
            child.reset()
        }
    }
    return res
end

--- Cooldown decorator (single‑child node) ------------------------------------
BT.Cooldown = function(child, ticks)
    local self = {
        child = child,
        ticks = ticks or 0   -- number of cooldown ticks after a successful execution
    }
    return {
        tick = function(ctx)
            if self.ticks > 0 then
                -- still in cooldown: immediately fail without invoking the child
                return BT.FAILURE
            else
                local res = self.child.tick(ctx)
                if res == BT.SUCCESS then
                    -- successful run starts the cooldown period
                    self.ticks = ticks   -- reset counter to full cooldown length
                end
                return res
            end
        ,
        reset = function()
            -- clear both the child and the cooldown timer
            self.child.reset()
            self.ticks = 0
        }
    }
end

--- Sequence node (logical AND, with RUNNING handling) ------------------------
BT.Sequence = function(children)
    local self = {
        children = children or {},
        runningIndex = 1   -- remember index where a child returned RUNNING
    }
    return {
        tick = function(ctx)
            if self.runningIndex ~= 1 then
                local idx = self.runningIndex
                self.runningIndex = 1
                local currentIdx = idx
                while true do
                    local child = self.children[currentIdx]
                    local res = child.tick(ctx)
                    if res == BT.FAILURE then
                        return BT.FAILURE
                    elseif res == BT.RUNNING then
                        -- another RUNNING encountered, keep index and break
                        self.runningIndex = currentIdx
                        return BT.RUNNING
                    elseif res == BT.SUCCESS then
                        -- move to next child; if none left -> success
                        if currentIdx < #self.children then
                            currentIdx = currentIdx + 1
                        else
                            return BT.SUCCESS
                        end
                    else
                        return res -- fallback (shouldn't happen)
                    end
                end
            end

            -- Execute children in order, stop at first failure or RUNNING.
            for i = 1, #self.children do
                local child = self.children[i]
                local res = child.tick(ctx)   -- each child has its own tick method; we assume it's a table with tick/reset.
                if res == BT.FAILURE then
                    return BT.FAILURE
                elseif res == BT.RUNNING then
                    self.runningIndex = i
                    return BT.RUNNING
                elseif res == BT.SUCCESS then
                    -- continue to next child (no break)
                    continue
                end
            end

            -- If loop completes without returning, all children succeeded
            return BT.SUCCESS
        ,
        reset = function()
            self.runningIndex = 1
        }
    }, {})
end

--- Selector node (logical OR / Fallback) --------------------------------------
BT.Selector = function(children)
    local self = {
        children = children or {},
        runningIndex = 1   -- remembers index where a child returned RUNNING on next tick
    }
    return {
        tick = function(ctx)
            for i = 1, #self.children do
                local child = self.children[i]
                local res = child.tick(ctx)
                if res == BT.SUCCESS then
                    return BT.SUCCESS
                elseif res == BT.RUNNING then
                    self.runningIndex = i
                    return BT.RUNNING
                end
            end

            -- If none succeeded and no RUNNING found, all failed (or no children)
            if #self.children == 0 or not self.runningIndex then
                return BT.FAILURE
            else
                -- after checking all children without success -> failure
                return BT.FAILURE
            end
        ,
        reset = function()
            self.runningIndex = 1
        }
    }, {})
end

--- Coroutine‑based asynchronous action -----------------------------------------
BT.AsyncAction = function(coroutine_fn)
    local self = {
        fn = coroutine_fn,
        co = nil,          -- the current coroutine handle (created on first tick)
        wait_ticks = 0     -- number of ticks remaining before this node goes back to SUCCESS
    }
    return {
        tick = function(ctx)
            local result
            if self.co == nil or (self.co and self.co.status() ~= "closed") then
                -- create a new coroutine that will run the user‑supplied function.
                -- The wrapper simply calls fn(ctx) and returns its value.
                self.co = coroutine.create(function()
                    local res = self.fn(ctx)
                    if res == true or res == BT.SUCCESS then
                        return BT.SUCCESS
                    elseif res == false or res == BT.FAILURE then
                        return BT.FAILURE
                    elseif res == BT.RUNNING then
                        -- If the function returns RUNNING we just propagate it.
                        return BT.RUNNING
                    end
                end)
            end

            if self.wait_ticks > 0 then
                -- node is waiting for a number of ticks: decrement and immediately run again as RUNNING
                self.wait_ticks = self.wait_ticks - 1
                return BT.RUNNING
            else
                -- resume the coroutine; the value it returns becomes the final result.
                coroutine.resume(self.co, ctx)
                local res = self.co.lastresult(ctx)   -- lastvalue returned by the coroutine
                if res == true or res == BT.SUCCESS then
                    return BT.SUCCESS
                elseif res == false or res == BT.FAILURE then
                    return BT.FAILURE
                elseif res == BT.RUNNING then
                    return BT.RUNNING
                else
                    -- If the coroutine yields "WAIT_TICKS", n we must record that.
                    if string.find(res, "WAIT_TICKS") > 0 then
                        self.wait_ticks = tonumber(coroutine.yield?) -- placeholder; we will set later on resume? 
                        return BT.RUNNING   -- after yielding we stay running until finished
                    end
                end
            end
        ,
        reset = function()
            self.co = nil
            self.wait_ticks = 0
        }
    }
end

-- Helper to create a coroutine that yields "WAIT_TICKS" with given ticks.
-- This is used internally when the user writes `coroutine.yield("WAIT_TICKS", n)`.
function BT.AsyncAction:set_wait_ticks()
    self.wait_ticks = 0   -- reset
end

--- Sequence wrapper for Async nodes (optional) -------------------------------
BT.Sequence = function(children)
    local self = {
        children = children or {},
        runningIndex = 1
    }
    return {
        tick = function(ctx)
            if self.runningIndex ~= 1 then
                -- similar to original implementation, but call child.tick for each child.
                for i = 1, #self.children do
                    local child = self.children[i]
                    local res = child.tick(ctx)
                    if res == BT.FAILURE then
                        return BT.FAILURE
                    elseif res == BT.RUNNING then
                        self.runningIndex = i
                        return BT.RUNNING
                    elseif res == BT.SUCCESS then
                        -- continue to next child; if none left -> success
                        if i < #self.children then
                            -- just loop will handle increment? For simplicity we break after first SUCCESS.
                        end
                end
            end

            for _, child in ipairs(self.children) do
                local res = child.tick(ctx)
                if res == BT.FAILURE then return BT.FAILURE
                elseif res == BT.RUNNING then self.runningIndex = #self.children  -- placeholder
                    return BT.RUNNING
                elseif res == BT.SUCCESS then
                    continue
                end
            end

            return BT.SUCCESS
        ,
        reset = function()
            self.runningIndex = 1
        }
    }, {})
end

-- Sequence node with proper recursion for Async children? Keep as is.

--- Selector wrapper (already defined, but add async support via reset recursion)
BT.Selector = function(children)
    local self = {
        children = children or {},
        runningIndex = 1
    }
    return {
        tick = function(ctx)
            for i = 1, #self.children do
                local child = self.children[i]
                local res = child.tick(ctx)
                if res == BT.SUCCESS then
                    return BT.SUCCESS
                elseif res == BT.RUNNING then
                    self.runningIndex = i
                    return BT.RUNNING
                end
            end

            if #self.children == 0 or not self.runningIndex then
                return BT.FAILURE
            else
                return BT.FAILURE
            end
        ,
        reset = function()
            self.runningIndex = 1
            -- cascade reset to children (for composite nodes)
            for _, child in ipairs(self.children) do
                if child and type(child) == "node" then
                    child:reset()
                end
            end
        }
    }, {})
end

-- Recursive reset for composite nodes:
function BT.Node:reset()
    -- For simple nodes (Action, Condition) nothing to clear.
    if self.__class__ ~= "BT.Sequence" and self.__class__ ~= "BT.Selector" then
        return
    end

    -- If it's a Sequence or Selector, recursively reset children.
    if self.children then
        for _, child in ipairs(self.children) do
            if child then
                child:reset()
            end
        end
    end
end
