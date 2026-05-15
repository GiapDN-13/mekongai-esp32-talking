# RAGFlow Agent APIs and Dify-compatible retrieval

## 1. Dify-compatible retrieval — `retrieval`

**Description:** Knowledge retrieval in a Dify-like shape so existing Dify clients can call RAGFlow. Supports text / hybrid retrieval and metadata filters.

**Method:** `POST`  
**URL:** `/api/v1/dify/retrieval`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| knowledge_id | string | yes | — | Dataset (knowledge base) id |
| query | string | yes | — | Search query |
| use_kg | boolean | no | false | Whether to use the knowledge graph |
| retrieval_setting | object | no | `{}` | Score threshold and top-k |
| metadata_condition | object | no | `{}` | Document metadata filter |

**`retrieval_setting` example:**

```json
{
  "score_threshold": 0.5,
  "top_k": 5
}
```

**`metadata_condition` example:**

```json
{
  "logic": "and",
  "conditions": [
    {
      "name": "author",
      "comparison_operator": "eq",
      "value": "Alice"
    }
  ]
}
```

### Response

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "records": [
      {
        "content": "RAGFlow is a retrieval-augmented generation engine...",
        "score": 0.92,
        "title": "RAGFlow_Introduction.pdf",
        "metadata": {
          "doc_id": "doc_uuid_123",
          "author": "Alice",
          "publish_year": "2024"
        }
      }
    ]
  }
}
```

---

## 2. Create Agent session — `create_agent_session`

**Description:** Creates an Agent session: context container for messages and DSL state.

**Method:** `POST`  
**URL:** `/api/v1/agents/<agent_id>/sessions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Query parameters

| Field | Type | Required | Description |
|---|---|---|---|
| user_id | string | no | End-user id; defaults to tenant if omitted |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "session_uuid_new_123",
    "agent_id": "agent_uuid_abc",
    "user_id": "user_123",
    "source": "agent",
    "dsl": { },
    "messages": [
      {
        "role": "assistant",
        "content": "Hi! I am your assistant. How can I help?"
      }
    ]
  }
}
```

---

## 3. List Agent sessions — `list_agent_session`

**Description:** Paged sessions for an agent; filter by session id or user id.

**Method:** `GET`  
**URL:** `/api/v1/agents/<agent_id>/sessions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page |
| page_size | int | no | 30 | Page size |
| orderby | string | no | `"update_time"` | Sort field |
| desc | boolean | no | true | Descending |
| id | string | no | — | Exact session id |
| user_id | string | no | — | Filter by user |
| dsl | boolean | no | true | Include full DSL in each row (large payload) |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "session_uuid_123",
      "agent_id": "agent_uuid_abc",
      "user_id": "user_123",
      "create_time": 1715000000000,
      "update_time": 1715000050000,
      "source": "agent",
      "messages": [
        { "role": "assistant", "content": "Hi there!" },
        { "role": "user", "content": "What is RAG?" }
      ]
    }
  ]
}
```

---

## 4. Delete Agent sessions — `delete_agent_session`

**Description:** Deletes agent sessions in batch.

**Method:** `DELETE`  
**URL:** `/api/v1/agents/<agent_id>/sessions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| ids | array\<string\> | no | Session ids. If omitted, behavior may clear all sessions for the agent — use with care. |

**Example:**

```json
{
  "ids": ["session_id_1", "session_id_2"]
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "success_count": 2,
    "errors": []
  }
}
```

---

## 5. Agent completion (streaming) — `agent_completions`

**Description:** Sends a user turn to the Agent; core interactive API with **SSE**. The graph runs nodes (retrieval, LLM, tools, etc.) and can stream partial output. Set `return_trace` for per-node trace events.

**Method:** `POST`  
**URL:** `/api/v1/agents/<agent_id>/completions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| session_id | string | yes | — | Session from create API |
| question | string | yes | — | User message |
| stream | boolean | no | true | Use SSE (recommended) |
| return_trace | boolean | no | false | Include `node_finished` trace payloads |

### Response (stream)

**Content-Type:** `text/event-stream`

Each line: `data:` + JSON.

**Event kinds:**
- `message` — text delta
- `node_finished` — when `return_trace=true`, node output
- `message_end` — end of assistant turn
- `[DONE]` — stream end

**Examples:**

```text
data:{"code": 0, "message": "success", "data": {"content": "Hello", "reference": {}, "id": "msg_uuid_1"}, "event": "message"}

data:{"code": 0, "message": "success", "data": {"component_id": "retrieval_node_1", "content": "...", "trace": []}, "event": "node_finished"}

data:[DONE]
```

### Response (non-stream)

When `stream=false`, returns one JSON object after the run finishes.

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "content": "Hello world! This is the final answer.",
    "reference": { },
    "trace": []
  }
}
```
