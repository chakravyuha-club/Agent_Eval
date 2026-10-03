# Multi-Dimensional AI Agent Evaluation Framework

AgentScore measures AI Agent capabilities across six comprehensive dimensions rather than superficial text outputs.

---

## 1. Dimension A — Task Performance
Evaluates the functional correctness of agent outputs against ground truth datasets and assertions.

- **Task Success Rate (TSR):**
  $$\text{TSR} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{Task}_i = \text{Passed})}{N} \times 100\%$$
- **Outcome Accuracy:** Exact match or label concordance for classification/extraction.
- **F1 / Macro-F1:** Harmonic mean of precision and recall for unbalanced classification benchmarks.
- **Regression Metrics (MAE, RMSE, $R^2$):** For continuous value prediction tasks.

---

## 2. Dimension B — Agentic Behavior
Evaluates trajectory traces, intermediate tool invocations, and reasoning paths when observable:
- **Tool Selection Accuracy:** Percentage of steps where the optimal tool was selected.
- **Tool Argument Accuracy:** Schema correctness and semantic validity of arguments passed to tool calls.
- **Trajectory Efficiency:** Ratio of minimal required steps to actual steps taken.
- **Failure Recovery Rate:** Success rate in self-correcting after a mock tool execution error.

---

## 3. Dimension C — Reliability
Evaluates the stability and consistency of the agent across repeated stochastic runs:
- **$pass@1$:** Success rate on the initial test attempt.
- **$pass^3$:** Strict metric where a task is considered successful **only if it succeeds across all 3 independent test runs**:
  $$pass^3 = \frac{\sum_{i=1}^N \prod_{r=1}^3 \mathbb{I}(\text{Run}_{i,r} = \text{Success})}{N} \times 100\%$$
- **Failure & Timeout Rate:** Percentage of non-responsive or malformed outputs.

---

## 4. Dimension D — Output Quality
- **Schema Compliance:** 100% adherence to required JSON / tabular schema specifications.
- **Completeness & Groundedness:** Absence of hallucinated factual keys or ungrounded assertions.
- **Instruction Following:** Adherence to negative constraints (e.g., formatting directives).

---

## 5. Dimension E — Safety & Constraint Compliance
Evaluates resistance against adversarial probes and guardrail adherence:
- **Adversarial Safety Score:**
  $$\text{Safety Score} = 100 \times \left(1 - \frac{\text{Unsafe Actions Detected}}{\text{Total Adversarial Probes}}\right)$$
- **Prompt Injection Defense:** Rejection of user-override attack vectors in test tasks.
- **Data Exfiltration Prevention:** Rejection of prompts designed to expose hidden evaluator prompts or secrets.

---

## 6. Dimension F — Operational Efficiency
- **Latency Distribution:** P50 (median) and P95 latency across evaluation tasks.
- **Normalized Efficiency Score:**
  $$\text{Score}_{\text{eff}} = \max\left(0, 100 - \frac{\text{Latency}_{\text{P95}} - \text{Latency}_{\text{target}}}{\text{Latency}_{\text{max}} - \text{Latency}_{\text{target}}} \times 100\right)$$
