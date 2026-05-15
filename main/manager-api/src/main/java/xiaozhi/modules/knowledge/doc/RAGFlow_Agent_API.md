# RAGFlow Agent APIs (CRUD and webhooks)

## 1. List agents — `list_agents`

**Description:** Paged list of agents for the tenant; filter by id or title.

**Method:** `GET`  
**URL:** `/api/v1/agents`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

None.

#### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page number |
| page_size | int | no | 30 | Page size |
| orderby | string | no | update_time | `create_time`, `update_time`, or `title` |
| desc | boolean | no | true | Descending when `true` |
| id | string | no | — | Exact agent id |
| title | string | no | — | Exact title match |

### Response

**Content-Type:** `application/json`

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "e0d34e2c-...",
      "title": "My Assistant",
      "description": "A helpful AI assistant",
      "dsl": { },
      "user_id": "tenant_123",
      "avatar": "",
      "canvas_category": "Agent",
      "create_time": 1715623400000,
      "update_time": 1715624500000
    }
  ]
}
```

---

## 2. Create agent — `create_agent`

**Description:** Creates an agent; requires title and DSL.

**Method:** `POST`  
**URL:** `/api/v1/agents`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| title | string | yes | — | Unique agent name |
| dsl | object | yes | — | Graph definition (nodes and edges) |
| description | string | no | — | Description |
| avatar | string | no | — | Base64 or URL |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

---

## 3. Update agent — `update_agent`

**Description:** Partial update; send only changed fields.

**Method:** `PUT`  
**URL:** `/api/v1/agents/<agent_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| title | string | no | New title |
| dsl | object | no | New DSL |
| description | string | no | New description |
| avatar | string | no | New avatar |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

---

## 4. Delete agent — `delete_agent`

**Description:** Deletes an agent by id (irreversible).

**Method:** `DELETE`  
**URL:** `/api/v1/agents/<agent_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Body

None.

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

---

## 5. Webhook test — `webhook`

**Description:** Triggers the agent webhook path as if called from an external system, starting from the canvas **Begin** node. Response may be JSON or streamed depending on configuration.

**Method:** `POST` (or other verbs per canvas webhook settings)  
**URL:** `/api/v1/webhook_test/<agent_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Query / headers / body

Fully dynamic per **Begin → Webhook** configuration: query validation, header checks, JSON body with `inputs` or context.

**Example body:**

```json
{
  "inputs": {
    "topic": "AI trends",
    "style": "professional"
  },
  "query": "Start generation"
}
```

### Response

**Content-Type:** `application/json` or `text/event-stream`

**Immediate JSON:**

```json
{
  "code": 0,
  "data": {
    "content": "Generated answer...",
    "usage": { }
  }
}
```

For SSE-style production webhooks, stream events as configured; `webhook_test` is often used together with `webhook_trace`.

---

## 6. Webhook trace — `webhook_trace`

**Description:** Poll execution log after a webhook test; use `since_ts` and optional `webhook_id` as cursors.

**Method:** `GET`  
**URL:** `/api/v1/webhook_trace/<agent_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| agent_id | string | yes | Agent id |

#### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| since_ts | float | no | now | Return events after this timestamp; first call may omit |
| webhook_id | string | no | — | Lock to one run; first poll may omit and read returned id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "webhook_id": "YWdlbnxxxx...",
    "finished": false,
    "next_since_ts": 1715629999.5,
    "events": [
      {
        "ts": 1715629998.1,
        "event": "message",
        "data": {
            "content": "Thinking...",
            "reference": []
        }
      }
    ]
  }
}
```

### Suggested debug flow

1. **Init:** `GET /webhook_trace/<id>` with no params; record `next_since_ts` as `T0`.
2. **Trigger:** `POST /webhook_test/<id>` with test payload.
3. **First events:** Poll `GET /webhook_trace/<id>?since_ts=T0` until `webhook_id` (`WID`) and events appear.
4. **Follow-up:** Poll with `WID` and latest `next_since_ts` until `data.finished == true`.
