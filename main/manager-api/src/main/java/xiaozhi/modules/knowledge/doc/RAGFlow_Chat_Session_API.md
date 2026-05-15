# RAGFlow chat assistant session APIs

## 1. Create session — `create` (create chat session)

**Description:** Creates a session for a chat assistant. The assistant opener is injected as the first assistant message.

**Method:** `POST`  
**URL:** `/api/v1/chats/<chat_id>/sessions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant (dialog) id |

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| name | string | no | `"New session"` | Session display name |
| user_id | string | no | — | End-user id for multi-user scenarios |

**Example:**

```json
{
  "name": "RAG consultation",
  "user_id": "client_001"
}
```

### Response

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "session_uuid_123",
    "chat_id": "chat_uuid_abc",
    "name": "RAG consultation",
    "user_id": "client_001",
    "create_time": 1715000000000,
    "create_date": "2024-05-01 10:00:00",
    "update_time": 1715000000000,
    "update_date": "2024-05-01 10:00:00",
    "messages": [
      {
        "role": "assistant",
        "content": "Hi! I am your AI assistant. How can I help you today?"
      }
    ]
  }
}
```

---

## 2. List sessions — `list_session`

**Description:** Paged sessions for an assistant; filter by name, session id, or user id.

**Method:** `GET`  
**URL:** `/api/v1/chats/<chat_id>/sessions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant id |

#### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page number |
| page_size | int | no | 30 | Page size |
| orderby | string | no | `"create_time"` | Sort field |
| desc | boolean | no | true | Descending sort |
| name | string | no | — | Session name search |
| id | string | no | — | Exact session id |
| user_id | string | no | — | Filter by user id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "session_uuid_123",
      "chat_id": "chat_uuid_abc",
      "name": "RAG consultation",
      "user_id": "client_001",
      "create_time": 1715000000000,
      "create_date": "2024-05-01 10:00:00",
      "update_time": 1715000050000,
      "update_date": "2024-05-01 10:00:50",
      "messages": [
        {
          "role": "assistant",
          "content": "Hi! I am your AI assistant. How can I help you today?"
        },
        {
          "role": "user",
          "content": "What is RAGFlow?"
        }
      ]
    }
  ]
}
```

---

## 3. Update session — `update`

**Description:** Updates session metadata (typically **rename**). Message history is not modified through this API.

**Method:** `PUT`  
**URL:** `/api/v1/chats/<chat_id>/sessions/<session_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant id |
| session_id | string | yes | Session id |

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| name | string | no | New session name (non-empty) |

**Example:**

```json
{
  "name": "RAG technical discussion"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

## 4. Delete sessions — `delete`

**Description:** Deletes sessions under an assistant in batch.

**Method:** `DELETE`  
**URL:** `/api/v1/chats/<chat_id>/sessions`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| chat_id | string | yes | Assistant id |

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| ids | array\<string\> | no | Session ids to delete. If omitted, behavior may delete **all** sessions under the assistant — use with extreme care. |

**Example:**

```json
{
  "ids": ["session_uuid_123", "session_uuid_456"]
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

**Partial failure example:**

```json
{
  "code": 0,
  "message": "Partially deleted 1 sessions with 1 errors",
  "data": {
    "success_count": 1,
    "errors": ["The chat doesn't own the session session_uuid_999"]
  }
}
```
