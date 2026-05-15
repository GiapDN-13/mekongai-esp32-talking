# RAGFlow chat completion APIs (native, OpenAI-compatible, embedded chatbot)

## 1. Assistant completion (streaming) — `chat_completion`

**Description:** Sends a user turn to a chat assistant and returns the model reply with optional RAG. Primary native API; supports **SSE** when `stream` is true.

**Method:** `POST`  
**URL:** `/api/v1/chats/<chat_id>/completions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant id |

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| session_id | string | yes | — | Session id from session create API |
| question | string | yes | — | User message |
| stream | boolean | no | true | Stream tokens via SSE |
| quote | boolean | no | false | Include retrieval citations in the response |
| doc_ids | string | no | — | Comma-separated document ids to restrict retrieval |
| metadata_condition | object | no | `{}` | Metadata filter for retrieval |

### Response (stream)

**Content-Type:** `text/event-stream`

Each line is `data:` followed by a JSON object.

**Example:**

```text
data:{"code": 0, "message": "success", "data": {"answer": "Hello", "reference": {}}}

data:{"code": 0, "message": "success", "data": {"answer": " world!", "reference": {}}}

data:{"code": 0, "message": "success", "data": {"answer": "", "reference": {"chunk_1": {}}}}
```

### Response (non-stream)

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answer": "Hello world! This is the generated response.",
    "reference": {
      "chunk_id_1": {
        "content_with_weight": "Original text...",
        "doc_name": "manual.pdf"
      }
    }
  }
}
```

---

## 2. OpenAI-compatible chat — `chat_completion_openai_like`

**Description:** OpenAI-style `/v1/chat/completions` contract for a given assistant id. Usable from LangChain, OpenAI SDKs, etc.

**Method:** `POST`  
**URL:** `/api/v1/chats_openai/<chat_id>/chat/completions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant id (part of the logical “base URL”) |

#### Body (OpenAI-style JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| messages | array | yes | Chat messages with `role` and `content` |
| model | string | yes | Any non-empty string (assistant’s configured model is used) |
| stream | boolean | no | Default often `true` |

**Example:**

```json
{
  "model": "ragflow_default",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum physics."}
  ],
  "stream": true
}
```

### Response (stream)

**Content-Type:** `text/event-stream`

OpenAI chunk format:

```text
data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1715000000, "model": "model", "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": null}]}

data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1715000001, "model": "model", "choices": [{"index": 0, "delta": {"content": "Quantum"}, "finish_reason": null}]}

data: [DONE]
```

---

## 3. Embedded chatbot completion — `chatbot_completions`

**Description:** For **embed widgets** on third-party sites. Uses `Authorization: Bearer <API_KEY>` (beta/embed token) and targets a dialog id.

**Method:** `POST`  
**URL:** `/api/v1/chatbots/<dialog_id>/completions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| dialog_id | string | yes | Dialog (assistant) id |

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| question | string | yes | — | User message |
| stream | boolean | no | true | SSE stream |
| session_id | string | no | — | Session id for context |
| quote | boolean | no | false | Include citations |

### Response (stream)

**Content-Type:** `text/event-stream`

Same general shape as native `chat_completion` SSE.

```text
data:{"code": 0, "message": "success", "data": {"answer": "Here is the answer...", "reference": {}}}
```

---

## 4. Embedded chatbot info — `chatbots_inputs`

**Description:** Returns widget bootstrap data: title, avatar, prologue.

**Method:** `GET`  
**URL:** `/api/v1/chatbots/<dialog_id>/info`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| dialog_id | string | yes | Dialog id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "title": "IT Support Bot",
    "avatar": "http://...",
    "prologue": "Hi! How can I help?"
  }
}
```
