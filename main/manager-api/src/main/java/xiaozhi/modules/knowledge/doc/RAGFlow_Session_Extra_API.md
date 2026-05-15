# RAGFlow SearchBot extras and generic session helpers

## 1. Citation / search-app detail — `detail_share_embedded`

**Description:** Used when the UI opens a citation or search-app panel for a SearchBot. Returns SearchBot configuration (title, linked KBs, search settings). Actual chunk text is usually already in the `ask` response `reference` field.

**Method:** `GET`  
**URL:** `/api/v1/searchbots/detail`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Query parameters

| Field | Type | Required | Description |
|---|---|---|---|
| search_id | string | yes | SearchBot / search application id |

### Response

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "search_app_uuid_123",
    "title": "IT Knowledge Base",
    "description": "Tech support search bot",
    "kb_ids": ["kb_uuid_1", "kb_uuid_2"],
    "search_config": {
      "top_k": 5,
      "similarity_threshold": 0.5
    }
  }
}
```

---

## 2. SearchBot retrieval test — `retrieval_test_embedded`

**Description:** Runs retrieval only (no LLM answer) for debugging SearchBot parameters (threshold, top-k, etc.).

**Method:** `POST`  
**URL:** `/api/v1/searchbots/retrieval_test`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| kb_id | string or array | yes | — | Dataset id or list of ids |
| question | string | yes | — | Test query |
| page | int | no | 1 | Page number |
| size | int | no | 30 | Page size |
| doc_ids | array\<string\> | no | — | Restrict to these documents |
| similarity_threshold | float | no | 0.0 | Minimum similarity |
| top_k | int | no | 1024 | Max chunks |
| highlight | boolean | no | false | Highlight query terms in snippets |

**Example:**

```json
{
  "kb_id": ["dataset_uuid_1"],
  "question": "refund policy",
  "top_k": 5,
  "highlight": true
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 12,
    "chunks": [
      {
        "content_with_weight": "Refunds are processed within <em>7 days</em>...",
        "doc_name": "policy.pdf",
        "doc_id": "doc_uuid_101",
        "similarity": 0.92,
        "img_id": ""
      }
    ],
    "labels": []
  }
}
```

---

## 3. Generic session ask — `ask_about`

**Description:** **Internal / console-style** Q&A: user token auth, explicit `dataset_ids`, not tied to a saved Chat/Agent/SearchBot profile.

**Method:** `POST`  
**URL:** `/api/v1/sessions/ask`  
**Auth:** Header `Authorization: Bearer <USER_TOKEN>`

### Request

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| question | string | yes | User question |
| dataset_ids | array\<string\> | yes | Dataset ids the user may access |

**Example:**

```json
{
  "question": "Summary of report",
  "dataset_ids": ["dataset_uuid_internal_1"]
}
```

### Response (stream)

**Content-Type:** `text/event-stream`

```text
data:{"code": 0, "message": "", "data": {"answer": "Here is the summary:", "reference": {}}}

data:{"code": 0, "message": "", "data": {"answer": " The report indicates...", "reference": {}}}

data:{"code": 0, "message": "", "data": true}
```

---

## 4. Generic related questions — `related_questions`

**Description:** **Internal / test** related-question suggestions from the LLM, optionally scoped by industry label.

**Method:** `POST`  
**URL:** `/api/v1/sessions/related_questions`  
**Auth:** Header `Authorization: Bearer <USER_TOKEN>`

### Request

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| question | string | yes | — | Seed question or keywords |
| industry | string | no | `""` | Hint such as `"Finance"` or `"Healthcare"` |

**Example:**

```json
{
  "question": "Data privacy",
  "industry": "IT"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": [
    "GDPR compliance checklist",
    "Data encryption standards",
    "User consent management"
  ]
}
```
