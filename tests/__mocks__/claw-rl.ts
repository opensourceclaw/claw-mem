// Mock for claw-rl
export class RuleEngine {
  state = {
    successRate: 0,
    totalFeedback: 0,
  };

  collectFeedback(feedback: { task: string; result: string; success: boolean; tool: string }) {
    this.state.totalFeedback++;
    if (feedback.success) {
      this.state.successRate = this.state.totalFeedback > 0 
        ? (this.state.successRate * (this.state.totalFeedback - 1) + 1) / this.state.totalFeedback
        : 1;
    }
  }
}
