# RAGFlow SearchBot and AgentBot APIs

## 1. SearchBot ask — `ask_about_embedded`

**Description:** Main SearchBot Q&A for embed scenarios. Retrieves from `kb_ids` and answers; uses `Authorization: Bearer <API_KEY>` (embed/beta token).

**Method:** `POST`  
**URL:** `/api/v1/searchbots/ask`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| question | string | yes | — | User question |
| kb_ids | array\<string\> | yes | — | Dataset ids to search |
| search_id | string | no | — | Optional Search App id to apply saved search config |

**Example:**

```json
{
  "question": "What is the refund policy?",
  "kb_ids": ["dataset_uuid_1", "dataset_uuid_2"],
  "search_id": "search_app_uuid_abc"
}
```

### Response (stream)

**Content-Type:** `text/event-stream`

```text
data:{"code": 0, "message": "", "data": {"answer": "According to the ", "reference": {}}}

data:{"code": 0, "message": "", "data": {"answer": "policy, refunds are processed within 7 days.", "reference": {"chunk_1": {"content_with_weight": "Refunds...", "doc_name": "policy.pdf"}}}}

data:{"code": 0, "message": "", "data": true}
```

---

## 2. Mind map — `mindmap`

**Description:** Builds a tree structure for UI mind-map visualization from a question and knowledge bases.

**Method:** `POST`  
**URL:** `/api/v1/searchbots/mindmap`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| question | string | yes | Topic or question |
| kb_ids | array\<string\> | yes | Dataset ids |
| search_id | string | no | Search App id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "root": {
      "text": "Refund Policy",
      "children": [
        {
          "text": "Conditions",
          "children": [
            { "text": "Product defect" },
            { "text": "Shipping error" }
          ]
        },
        {
          "text": "Timeline",
          "children": [
            { "text": "7-14 business days" }
          ]
        }
      ]
    }
  }
}
```

---

## 3. Related questions (embed) — `related_questions_embedded`

**Description:** Suggested follow-up questions for the current query (e.g. “People also ask”).

**Method:** `POST`  
**URL:** `/api/v1/searchbots/related_questions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| question | string | yes | Current user question |
| search_id | string | no | Search App id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": [
    "How to apply for a refund online?",
    "What items are non-refundable?",
    "Contact customer support"
  ]
}
```

---

## 4. AgentBot begin inputs — `begin_inputs`

**Description:** Returns AgentBot bootstrap data, especially **Begin** node variables as a form schema (name, email, etc.) before the first turn.

**Method:** `GET`  
**URL:** `/api/v1/agentbots/<agent_id>/inputs`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "title": "Booking Assistant",
    "avatar": "http://...",
    "prologue": "Welcome! Please tell me your details.",
    "inputs": {
      "user_name": {
        "type": "string",
        "description": "Your Name",
        "required": true
      },
      "email": {
        "type": "string",
        "description": "Contact Email",
        "required": false
      }
    },
    "mode": "chat"
  }
}
```

---

## 5. AgentBot completion — `agent_bot_completions`

**Description:** Embedded Agent chat for end users (API key auth). Same graph execution as server Agent, streaming by default.

**Method:** `POST`  
**URL:** `/api/v1/agentbots/<agent_id>/completions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| session_id | string | yes | Session id |
| inputs | object | no | Values for Begin variables, e.g. `{"user_name": "Alice"}` |
| query | string | no | User message |
| stream | boolean | no | Default `true` |

**Example:**

```json
{
  "session_id": "session_uuid_123",
  "inputs": {
    "user_name": "Bob"
  },
  "query": "I want to book a room.",
  "stream": true
}
```

### Response (stream)

```text
data:{"event": "message", "data": {"content": "Hello Bob, ", "reference": {}}}

data:{"event": "message", "data": {"content": "when do you want to check in?", "reference": {}}}
```

---

## 6. Agent OpenAI-compatible completion — `agents_completion_openai_compatibility`

**Description:** OpenAI `/chat/completions`-shaped API for an Agent id.

**Method:** `POST`  
**URL:** `/api/v1/agents_openai/<agent_id>/chat/completions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Body (OpenAI-style)

| Field | Type | Required | Description |
|---|---|---|---|
| messages | array | yes | Roles and content |
| model | string | yes | Placeholder string |
| stream | boolean | no | Default `true` |

### Response (stream)

```text
data: {"id": "agent-chat-uuid", "object": "chat.completion.chunk", "created": 1715000000, "model": "ragflow_agent", "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": null}]}

data: {"id": "agent-chat-uuid", "object": "chat.completion.chunk", "created": 1715000001, "model": "ragflow_agent", "choices": [{"index": 0, "delta": {"content": "Processing your request..."}, "finish_reason": null}]}

data: [DONE]
```
