# RAGFlow dataset (knowledge base) APIs

## 1. Create dataset — `create`

**Description:** Creates a dataset for documents and retrieval. Configure embedding model, default chunking, and permissions.

**Method:** `POST`  
**URL:** `/api/v1/datasets`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Path parameters

None.

#### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| name | string | yes | — | Unique name within the tenant |
| avatar | string | no | `""` | Base64 image |
| description | string | no | `""` | Short description |
| embedding_model | string | no | (system default) | Embedding model id (e.g. `BAAI/bge-large-zh-v1.5`) |
| permission | string | no | `"me"` | `me` (private) or `team` (shared) |
| chunk_method | string | no | `"naive"` | Default chunking when upload omits method: `naive`, `manual`, `qa`, `table`, `paper`, `book`, `laws`, `presentation`, `picture`, `one`, `email`, … |
| parser_config | object | no | (see below) | Parser options |

**Default `parser_config` (naive):**

| Field | Type | Default | Description |
|---|---|---|---|
| chunk_token_num | int | 512 | Max tokens per chunk |
| delimiter | string | `"\\n"` | Paragraph delimiter |
| layout_recognize | string | `"DeepDOC"` | Layout model (`DeepDOC` / `Simple`) |
| html4excel | boolean | false | Convert Excel to HTML |
| auto_keywords | int | 0 | Keywords per chunk; 0 = off |
| auto_questions | int | 0 | Questions per chunk; 0 = off |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "kb_uuid_12345678",
    "name": "Product manuals",
    "avatar": "",
    "tenant_id": "tenant_001",
    "description": "All product documentation",
    "embedding_model": "BAAI/bge-large-zh-v1.5",
    "permission": "me",
    "chunk_method": "naive",
    "parser_config": {
      "chunk_token_num": 512,
      "delimiter": "\n",
      "layout_recognize": "DeepDOC",
      "html4excel": false,
      "auto_keywords": 0,
      "auto_questions": 0
    },
    "chunk_count": 0,
    "document_count": 0,
    "create_time": 1715623400000,
    "update_time": 1715624500000
  }
}
```

---

## 2. Delete datasets — `delete`

**Description:** Deletes one or more datasets and their documents/indexes (**irreversible**).

**Method:** `DELETE`  
**URL:** `/api/v1/datasets`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Request

#### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| ids | array\<string\> | yes | Dataset ids. **`null` may clear all datasets for the tenant** — extremely dangerous. |

**Example:**

```json
{
  "ids": ["kb_id_101", "kb_id_102"]
}
```

### Response

```json
{
  "code": 0,
  "message": "Successfully deleted 2 datasets, 0 failed...",
  "data": {
     "success_count": 2,
     "errors": []
  }
}
```

---

## 3. List datasets — `list_datasets`

**Description:** Lists datasets the caller (and team) can access, with paging and filters.

**Method:** `GET`  
**URL:** `/api/v1/datasets`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page (1-based) |
| page_size | int | no | 30 | Page size |
| orderby | string | no | `"create_time"` | `create_time`, `update_time`, `document_count` |
| desc | boolean | no | true | Descending when true |
| name | string | no | — | Fuzzy name |
| id | string | no | — | Exact dataset id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "kb_uuid_123",
      "name": "HR policies",
      "document_count": 12,
      "token_num": 10240,
      "chunk_count": 150,
      "create_time": 1715623400000,
      "permission": "team",
      "embedding_model": "BAAI/bge-large-zh-v1.5"
    }
  ],
  "total": 1
}
```

---

## 4. Update dataset — `update`

**Description:** Updates dataset settings. **`embedding_model` is usually locked** once chunks exist.

**Method:** `PUT`  
**URL:** `/api/v1/datasets/<dataset_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

#### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| dataset_id | string | yes | Dataset id |

#### Body (JSON)

All fields optional.

| Field | Type | Description |
|---|---|---|
| name | string | New unique name |
| avatar | string | Base64 avatar |
| description | string | New description |
| permission | string | `me` or `team` |
| embedding_model | string | Only when `chunk_count == 0` |
| chunk_method | string | Default for **new** uploads |
| parser_config | object | Replaces parser config |
| pagerank | int | 0 | Graph / ES weighting when applicable |

### Response

Returns updated dataset object (shape similar to create).

---

## 5. Knowledge graph — `knowledge_graph`

**Description:** Returns graph nodes and edges for visualization (e.g. force-directed chart).

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/knowledge_graph`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "graph": {
      "nodes": [
        {
          "id": "node_1",
          "label": "Artificial intelligence",
          "pagerank": 0.05,
          "color": "#fcb",
          "img": ""
        },
        {
          "id": "node_2",
          "label": "Machine learning",
          "pagerank": 0.03,
          "color": "#e2b"
        }
      ],
      "edges": [
        {
          "source": "node_1",
          "target": "node_2",
          "weight": 0.8,
          "label": "includes"
        }
      ]
    },
    "mind_map": {
        "root": {
            "id": "root_node",
            "children": []
        }
    }
  }
}
```

---

## 6. Delete knowledge graph — `delete_knowledge_graph`

**Description:** Removes graph index data (nodes/edges) for the dataset. **Does not** delete source documents or ordinary vector chunks. Rebuild with chunk/parse or `run_graphrag` as needed.

**Method:** `DELETE`  
**URL:** `/api/v1/datasets/<dataset_id>/knowledge_graph`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

---

## 7. Run GraphRAG — `run_graphrag`

**Description:** Starts an async GraphRAG build (entity/relationship extraction, community summaries). Requires parsed documents.

**Method:** `POST`  
**URL:** `/api/v1/datasets/<dataset_id>/run_graphrag`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

#### Body (JSON)

May be `{}`. Reserved fields:

| Field | Type | Default | Description |
|---|---|---|---|
| entity_types | array | `["organization", "person", "geo", "event"]` | Entity types to extract (reserved) |
| method | string | `"light"` | `light` / `general` / `complex` (reserved) |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "graphrag_task_id": "task_uuid_12345678"
  }
}
```

---

## 8. Run RAPTOR — `run_raptor`

**Description:** Starts async RAPTOR (recursive clustering + summarization) over chunks.

**Method:** `POST`  
**URL:** `/api/v1/datasets/<dataset_id>/run_raptor`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

#### Body (JSON)

May be `{}`. Reserved:

| Field | Type | Default | Description |
|---|---|---|---|
| max_cluster | int | 64 | Max clusters (reserved) |
| prompt | string | (built-in) | Summarization prompt (reserved) |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "raptor_task_id": "task_uuid_87654321"
  }
}
```

---

## 9. Trace GraphRAG — `trace_graphrag`

**Description:** Poll GraphRAG job status for the dataset.

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/trace_graphrag`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "task_uuid_12345678",
    "doc_id": "doc_uuid_...",
    "from_page": 0,
    "to_page": 10,
    "progress": 0.45,
    "progress_msg": "Extracting entities from chunk 25...",
    "create_time": 1715623400000,
    "update_time": 1715624500000
  }
}
```

`progress`: `0.0`–`1.0` (done at `1.0`); `-1.0` may indicate failure (verify against deployed server).

---

## 10. Trace RAPTOR — `trace_raptor`

**Description:** Poll RAPTOR job status.

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/trace_raptor`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "task_uuid_87654321",
    "progress": 1.0,
    "progress_msg": "Tree construction completed.",
    "create_time": 1715629000000
  }
}
```
