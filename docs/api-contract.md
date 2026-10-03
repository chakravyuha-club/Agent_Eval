# Stage 2 Deployed AI Agent API Contract

To participate in Stage 2 (Deployed Agent Evaluation), qualified teams must deploy an HTTP web service adhering strictly to this contract.

---

## 1. Health Check Endpoint

### `GET /health`
Used by the evaluator during pre-flight checks before executing evaluation suites.

**Response Status:** `200 OK`  
**Content-Type:** `application/json`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "agent_name": "Team01-AgenticModel"
}
```

---

## 2. Prediction & Action Endpoint

### `POST /predict`
The primary task execution endpoint invoked by the evaluator.

**Request Headers:**
- `Content-Type: application/json`
- `Accept: application/json`

**Request Body:**
```json
{
  "task_id": "eval_task_042",
  "stage": "stage_2",
  "input": {
    "query": "Find the optimal supplier with latency under 50ms and calculate total cost for 500 units.",
    "context": {
      "budget": 10000,
      "region": "us-east-1"
    }
  },
  "constraints": {
    "timeout_seconds": 10,
    "max_tool_calls": 5
  }
}
```

**Response Status:** `200 OK`  
**Content-Type:** `application/json`

```json
{
  "task_id": "eval_task_042",
  "status": "success",
  "prediction": {
    "selected_supplier_id": "supp_992",
    "total_cost": 4850.00,
    "estimated_latency_ms": 42
  },
  "explanation": "Supplier 992 meets the <50ms criteria with total cost of $4,850.",
  "trajectory": [
    {
      "step": 1,
      "tool": "search_suppliers",
      "args": { "region": "us-east-1", "max_latency": 50 },
      "output": "Found 3 suppliers: [supp_992, supp_104, supp_301]"
    },
    {
      "step": 2,
      "tool": "calculate_unit_pricing",
      "args": { "supplier_id": "supp_992", "units": 500 },
      "output": "Total: 4850"
    }
  ]
}
```

---

## 3. Error Response Contract
If an internal agent error occurs, return an informative error payload rather than crashing:

**Response Status:** `4xx` or `5xx`  
```json
{
  "task_id": "eval_task_042",
  "status": "error",
  "error": {
    "category": "tool_failure",
    "message": "Supplier inventory service temporarily unavailable."
  }
}
```
