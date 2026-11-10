local BT = {}

-- Execution statuses
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

-- Internal helper for state management in composite nodes
local function createNode(type, ...)
    local node = {}
    node.type = type
    node.__children = {...}
    return node
end

---------------------------------------------------
-- 1. Action Node
---------------------------------------------------
function BT.Action(fn)
    local node = createNode("Action", fn)

    function node:tick(ctx)
        local result = fn(ctx)
        if type(result) == "boolean" then
            return result and BT.SUCCESS or BT.FAILURE
        elseif result == BT.RUNNING then
            return BT.RUNNING
        end
        -- Assumes true or SUCCESS is implicitly handled if fn returns boolean for success case
        return result == true and BT.SUCCESS or BT.FAILURE
    end

    function node:reset()
        -- Actions usually don't have persistent state, but the method exists for interface consistency.
    end

    return node
end

---------------------------------------------------
-- 2. Condition Node
---------------------------------------------------
function BT.Condition(predicate)
    local node = createNode("Condition", predicate)

    function node:tick(ctx)
        local result = predicate(ctx)
        if result == true then
            return BT.SUCCESS
        else
            return BT.FAILURE
        end
    end

    function node:reset()
        -- Conditions usually don't have persistent state.
    end

    return node
end

---------------------------------------------------
-- 3. Sequence Node (AND logic)
---------------------------------------------------
function BT.Sequence(children)
    local node = createNode("Sequence", children)
    node._index = 1 -- Start at the first child

    function node:tick(ctx)
        for i = node._index, #children do
            local child = children[i]

            local result = child:tick(ctx)

            if result == BT.FAILURE then
                return BT.FAILURE
            elseif result == BT.RUNNING then
                -- Store current index to resume later
                node._index = i
                return BT.RUNNING
            end
            -- If SUCCESS, continue to the next child
        end

        -- If loop completes successfully
        return BT.SUCCESS
    end

    function node:reset()
        -- Reset index to start over on next tick
        node._index = 1
    end

    return node
end

---------------------------------------------------
-- 4. Selector Node (OR/Fallback logic)
---------------------------------------------------
function BT.Selector(children)
    local node = createNode("Selector", children)
    node._index = 1 -- Start at the first child

    function node:tick(ctx)
        for i = node._index, #children do
            local child = children[i]

            local result = child:tick(ctx)

            if result == BT.SUCCESS then
                return BT.SUCCESS
            elseif result == BT.RUNNING then
                -- Store current index to resume later
                node._index = i
                return BT.RUNNING
            end
            -- If FAILURE, continue to the next child (fall back)
        end

        -- If loop completes without finding a success
        return BT.FAILURE
    end

    function node:reset()
        -- Reset index to start over on next tick
        node._index = 1
    end

    return node
end

-- Example Usage (Optional - demonstrating structure setup)
-- local function moveAction(ctx)
--     print("Executing Move Action...")
--     return true -- Success
-- end

-- local function isTargetVisible(ctx)
--     print("Checking Visibility...")
--     return true -- Success
-- end

-- local function isAngry(ctx)
--     print("Checking Anger...")
--     return false -- Failure
-- end

-- local actionNode = BT.Action(moveAction)
-- local conditionNode = BT.Condition(isTargetVisible)
-- local angerCondition = BT.Condition(isAngry)

-- local sequenceTree = BT.Sequence({
--     actionNode,
--     conditionNode
-- })

-- print("\n--- Testing Sequence (Success Path) ---")
-- print("Tick 1:", sequenceTree:tick({}))

-- local selectorTree = BT.Selector({
--     conditionNode, -- This will fail
--     angerCondition, -- This will fail (if isAngry returns false)
-- })

-- print("\n--- Testing Selector (Failure Path) ---")
-- print("Tick 1:", selectorTree:tick({}))
