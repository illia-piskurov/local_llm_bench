BT = {}

BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

---@param fn function
BT.Action = {}
function BT.Action.tick(self, ctx)
  local result = self:fn(ctx)
  if result == true or result == BT.SUCCESS then
    return BT.SUCCESS
  elseif result == false or result == BT.FAILURE then
    return BT.FAILURE
  elseif result == BT.RUNNING then
    return BT.RUNNING
  else
    return BT.FAILURE
  end
end

function BT.Action.reset(self)
  -- No reset needed for Action nodes
end

---@param predicate function
BT.Condition = {}
function BT.Condition.tick(self, ctx)
  local result = self:predicate(ctx)
  if result then
    return BT.SUCCESS
  else
    return BT.FAILURE
  end
end

function BT.Condition.reset(self)
  -- No reset needed for Condition nodes
end

---@param children table{BT.Node}
BT.Sequence = {}
function BT.Sequence.tick(self, ctx)
  local child_index = 1
  local running = BT.RUNNING

  while running == BT.RUNNING do
    local node = self:getChild(child_index)
    if node then
      running = node:tick(ctx)
      if running == BT.FAILURE then
        return BT.FAILURE
      end
    else
      return BT.FAILURE -- Should not happen, but handle it
    end
    child_index = child_index + 1
  end

  return running
end

function BT.Sequence.getChild(self, index)
  local children = getchildren(self)
  if children and index > 0 and index <= #children then
    return children[index]
  else
    return nil
  end
end

function BT.Sequence.reset(self)
  -- Reset remembered child index to 1
  -- No actual reset needed, just a placeholder
end

---@param children table{BT.Node}
BT.Selector = {}
function BT.Selector.tick(self, ctx)
  local child_index = 1
  local running = BT.RUNNING

  while running == BT.RUNNING do
    local node = self:getChild(child_index)
    if node then
      running = node:tick(ctx)
      if running == BT.SUCCESS then
        return BT.SUCCESS
      end
    else
      return BT.FAILURE -- Should not happen, but handle it
    end
    child_index = child_index + 1
  end

  return running
end

function BT.Selector.getChild(self, index)
  local children = getchildren(self)
  if children and index > 0 and index <= #children then
    return children[index]
  else
    return nil
  end
end

function BT.Selector.reset(self)
  -- Reset remembered child index to 1
  -- No actual reset needed, just a placeholder
end
