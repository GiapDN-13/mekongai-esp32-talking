# RAGFlow chat assistant (app) APIs

## 1. Create assistant app — `create`

**Description:** Creates a new chat assistant. Supports linked knowledge bases, LLM parameters, prompt engine settings, and opener text.

**Method:** `POST`  
**URL:** `/api/v1/chats`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

None.

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| name | string | yes | — | Assistant name (unique within tenant) |
| avatar | string | no | — | Avatar URL or Base64 |
| description | string | no | `"A helpful Assistant"` | Short description |
| dataset_ids | array | no | `[]` | Linked dataset IDs (must be accessible to the tenant) |
| llm | object | no | — | LLM generation settings (model name, temperature, etc.) |
| prompt | object | no | — | Prompt engine and retrieval settings (system prompt, opener, rerank, etc.) |

**`llm` object:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| model_name | string | yes | — | Model id (e.g. `deepseek-chat`, `gpt-4`, `qwen-turbo`) |
| temperature | float | no | 0.1 | Sampling temperature (0.0–1.0) |
| top_p | float | no | 0.3 | Nucleus sampling threshold |
| max_tokens | int | no | 512 | Max tokens per reply |
| presence_penalty | float | no | 0.4 | Presence penalty (−2.0–2.0) |
| frequency_penalty | float | no | 0.7 | Frequency penalty (−2.0–2.0) |

**`prompt` object** (prompt + retrieval tuning):

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| prompt | string | no | (built-in) | **System prompt**. Role instructions; may use `{knowledge}` placeholder. |
| opener | string | no | `"Hi! I'm your assistant..."` | **Greeting** sent when the user opens the chat. |
| show_quote | boolean | no | true | **Show citations** in answers (e.g. `[1]`). |
| variables | array | no | `[{"key": "knowledge", "optional": false}]` | Variables for the system prompt; `knowledge` is reserved for retrieved chunks. |
| rerank_model | string | no | — | **Reranker model id** (e.g. `BAAI/bge-reranker-v2-m3`). |
| keywords_similarity_weight | float | no | 0.7 | **Keyword vs vector** mix (0.0–1.0); higher favors keyword match. |
| similarity_threshold | float | no | 0.2 | **Min similarity** for chunks; below threshold are dropped. |
| top_n | int | no | 6 | **Top N** chunks passed to the LLM. |
| empty_response | string | no | `"Sorry! No relevant..."` | Reply when retrieval returns nothing. |
| tts | boolean | no | false | Enable text-to-speech for assistant replies. |
| refine_multiturn | boolean | no | true | **Query rewrite** using history for better retrieval. |

### Response

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "e0d34e2c-1234-5678-9xxx-xxxxxxxxxxxx",
    "name": "Corporate KB assistant",
    "avatar": "http://example.com/avatar.png",
    "description": "Answers internal employee questions",
    "dataset_ids": ["kb_123", "kb_456"],
    "llm": {
      "model_name": "deepseek-chat",
      "temperature": 0.1,
      "top_p": 0.3,
      "max_tokens": 512,
      "presence_penalty": 0.4,
      "frequency_penalty": 0.7
    },
    "prompt": {
      "prompt": "You are an assistant. Answer using:\n{knowledge}",
      "opener": "Hi! How can I help?",
      "show_quote": true,
      "variables": [
        { "key": "knowledge", "optional": false }
      ],
      "rerank_model": "",
      "keywords_similarity_weight": 0.7,
      "similarity_threshold": 0.2,
      "top_n": 8,
      "empty_response": "No relevant answer was found in the knowledge base.",
      "tts": false,
      "refine_multiturn": true
    },
    "create_time": 1715623400000,
    "update_time": 1715624500000
  }
}
```

---

## 2. List assistants — `list_chat`

**Description:** Lists chat assistants for the tenant with paging, sort, and filters.

**Method:** `GET`  
**URL:** `/api/v1/chats`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

None.

#### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page number |
| page_size | int | no | 30 | Page size |
| orderby | string | no | create_time | Sort field (`create_time`, `update_time`) |
| desc | boolean | no | true | Descending when `true` |
| name | string | no | — | Fuzzy name filter |
| id | string | no | — | Exact id filter |

### Response

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "e0d34e2c-...",
      "name": "Support bot",
      "avatar": "http://...",
      "datasets": [
        {
          "id": "kb_1",
          "name": "Product manual",
          "avatar": "",
          "chunk_num": 100
        }
      ],
      "llm": { },
      "prompt": { },
      "create_time": 1715623400000
    }
  ]
}
```

---

## 3. Update assistant — `update`

**Description:** Updates an assistant; send only fields to change.

**Method:** `PUT`  
**URL:** `/api/v1/chats/<chat_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant id |

#### Body (JSON)

All fields optional.

| Field | Type | Description |
|---|---|---|
| name | string | New name |
| avatar | string | New avatar URL or Base64 |
| dataset_ids | array | **Replaces** linked dataset list entirely |
| llm | object | LLM config; must include `model_name` when sent |
| prompt | object | Prompt config; partial update supported |
| show_quotation | boolean | Show citations (root-level alias for `prompt.show_quote`) |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

## 4. Batch delete assistants — `delete_chats`

**Description:** Deletes one or more assistants by id.

**Method:** `DELETE`  
**URL:** `/api/v1/chats`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| ids | array\<string\> | yes | Assistant ids to delete. Prefer always sending explicit ids (avoid empty list in production). |

**Example:**

```json
{
  "ids": ["chat_id_1001", "chat_id_1002"]
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
