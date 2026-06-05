// Mock for claw-gov
export function createAction(action: string, type = "modify", metadata = {}) {
  return { action, type, metadata };
}

export function governAction(actionObj: ReturnType<typeof createAction>) {
  const isMalicious = actionObj.action.toLowerCase().includes("hack");
  return {
    approved: !isMalicious,
    violations: isMalicious ? ["L1: malicious intent"] : [],
    metadata: {
      layers_executed: ["L1", "L2", "L3"],
    },
  };
}
