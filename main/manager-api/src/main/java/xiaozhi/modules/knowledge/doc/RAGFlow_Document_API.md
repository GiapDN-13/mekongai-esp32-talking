# RAGFlow document and chunk APIs

## 1. Upload documents — `upload`

**Description:** Uploads one or more files into a dataset. Records are created with `run: UNSTART` and default parser settings from the dataset.

**Method:** `POST`  
**URL:** `/api/v1/datasets/<dataset_id>/documents`  
**Auth:** Header `Authorization: Bearer <API_KEY>`  
**Content-Type:** `multipart/form-data`

### Path parameters

| Field | Type | Required | Description |
|---|---|---|---|
| dataset_id | string | yes | Target dataset id |

### Form fields

| Field | Type | Required | Description |
|---|---|---|---|
| file | file | yes | Binary file(s). PDF, DOCX, TXT, MD, HTML, CSV, XLSX, PPTX, etc. Size limits depend on server config. |
| parent_path | string | no | Virtual folder path; default `/` (e.g. `/docs/v1/`) |

### Response

Array of document objects (see list response shape).

---

## 2. List documents — `list_docs`

**Description:** Paged documents in a dataset with filters.

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/documents`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page |
| page_size | int | no | 30 | Page size |
| orderby | string | no | `"create_time"` | `create_time`, `name`, `size`, … |
| desc | boolean | no | true | Newest/largest first when true |
| id | string | no | — | Exact document id |
| name | string | no | — | Exact file name |
| keywords | string | no | — | Fuzzy name match |
| suffix | array | no | — | Extensions: `pdf`, `docx`, … |
| run | array | no | — | `UNSTART`, `RUNNING`, `CANCEL`, `DONE`, `FAIL` |
| create_time_from | int | no | 0 | Created after (ms) |
| create_time_to | int | no | 0 | Created before (ms) |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 128,
    "docs": [
      {
        "id": "e457f92e3c0411ef8d4c0242ac120003",
        "thumbnail": null,
        "dataset_id": "d1234567890abcdef1234567890abcde",
        "chunk_method": "naive",
        "pipeline_id": null,
        "parser_config": {
          "chunk_token_num": 512,
          "delimiter": "\\n",
          "layout_recognize": "DeepDOC",
          "html4excel": false,
          "auto_keywords": 0,
          "auto_questions": 0,
          "topn_tags": 3,
          "raptor": { "use_raptor": false },
          "graphrag": { "use_graphrag": false }
        },
        "source_type": "local",
        "type": "pdf",
        "created_by": "user_id_123",
        "name": "UserGuide_v2.pdf",
        "location": "UserGuide_v2.pdf",
        "size": 102400,
        "token_count": 45000,
        "chunk_count": 120,
        "progress": 1.0,
        "progress_msg": "Parsing finished",
        "process_begin_at": "2024-05-13 10:05:00",
        "process_duration": 45.2,
        "meta_fields": { "author": "RAGFlow Team", "version": "2.0" },
        "suffix": "pdf",
        "run": "DONE",
        "status": "1",
        "create_time": 1715623400123,
        "create_date": "2024-05-13 10:03:20",
        "update_time": 1715623450000,
        "update_date": "2024-05-13 10:05:45"
      }
    ]
  }
}
```

---

## 3. Update document — `update_doc`

**Description:** Updates name, enabled flag, or parser settings. Changing `chunk_method` or `parser_config` resets `run` to `UNSTART` and clears existing chunks until re-parse.

**Method:** `PUT`  
**URL:** `/api/v1/datasets/<dataset_id>/documents/<document_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

Optional fields only.

| Field | Type | Description |
|---|---|---|
| name | string | New name; keep extension consistent with stored type |
| enabled | boolean | `true` → `status="1"`; `false` → excluded from retrieval |
| chunk_method | string | `naive`, `manual`, `qa`, `table`, `paper`, `book`, `laws`, `presentation`, `picture`, `one`, `knowledge_graph`, `email` |
| parser_config | object | Parser options (see naive table below) |

**Naive `parser_config`:**

| Field | Type | Default | Description |
|---|---|---|---|
| chunk_token_num | int | 512 | Max tokens per chunk |
| delimiter | string | `"\\n"` | Segment delimiter (escapes allowed) |
| layout_recognize | string | `"DeepDOC"` | `DeepDOC` or `Simple` |
| html4excel | boolean | false | Parse Excel as HTML tables |
| auto_keywords | int | 0 | 0 = off |
| auto_questions | int | 0 | 0 = off |
| topn_tags | int | 3 | Auto tag count |
| raptor | object | `{ "use_raptor": false }` | RAPTOR toggle |
| graphrag | object | `{ "use_graphrag": false }` | GraphRAG toggle |

---

## 4. Delete documents — `delete`

**Description:** Permanently removes documents, blobs, and index rows (**irreversible**).

**Method:** `DELETE`  
**URL:** `/api/v1/datasets/<dataset_id>/documents`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| ids | array\<string\> | yes | Document ids |

### Response

```json
{ "code": 0, "message": "success", "data": null }
```

---

## 5. Download original file — `download`

**Description:** Streams the stored binary; `Content-Disposition` attachment.

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/documents/<document_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

Binary body, `application/octet-stream`.

---

## 6. Start / retry parsing — `parse`

**Description:** Enqueues parse jobs for the given document ids (after upload or config change).

**Method:** `POST`  
**URL:** `/api/v1/datasets/<dataset_id>/chunks`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| document_ids | array\<string\> | yes | Documents to parse |

---

## 7. Stop parsing — `stop_parsing`

**Description:** Stops in-flight parse jobs for the listed documents.

**Method:** `DELETE`  
**URL:** `/api/v1/datasets/<dataset_id>/chunks`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| document_ids | array\<string\> | yes | Document ids |

---

## 8. List chunks — `list_chunks`

**Description:** Paged chunks for a document; optional full-text search in chunk bodies.

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/documents/<document_id>/chunks`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| page | int | no | 1 | Page |
| page_size | int | no | 30 | Page size |
| keywords | string | no | — | Search in chunk text |
| id | string | no | — | Exact chunk id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 150,
    "chunks": [
      {
        "id": "e457f92e3c0411ef8d4c0242ac120003_0",
        "content": "RAGFlow is an open-source RAG engine focused on deep document understanding...",
        "document_id": "doc_uuid_123",
        "docnm_kwd": "RAGFlow_UserGuide_v2.pdf",
        "important_keywords": ["RAGFlow", "DeepDOC", "LLM"],
        "questions": ["What is RAGFlow?"],
        "image_id": "",
        "dataset_id": "kb_uuid_456",
        "available": true,
        "positions": [1]
      }
    ],
    "doc": {
        "id": "doc_uuid_123",
        "name": "RAGFlow_UserGuide_v2.pdf",
        "chunk_count": 150,
        "token_count": 45000,
        "chunk_method": "naive",
        "run": "DONE",
        "status": "1",
        "progress": 1.0,
        "progress_msg": "Parsing finished",
        "dataset_id": "kb_uuid_456"
    }
  }
}
```

---

## 9. Add chunk — `add_chunk`

**Description:** Manually inserts a chunk; embeddings are computed server-side.

**Method:** `POST`  
**URL:** `/api/v1/datasets/<dataset_id>/documents/<document_id>/chunks`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| content | string | yes | Chunk text |
| important_keywords | array\<string\> | no | Keyword boost |
| questions | array\<string\> | no | Preset questions for QA mode |

---

## 10. Update chunk — `update_chunk`

**Description:** Updates chunk text, keywords, or `available`. Re-embeds when content changes.

**Method:** `PUT`  
**URL:** `/api/v1/datasets/<dataset_id>/documents/<document_id>/chunks/<chunk_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Description |
|---|---|---|
| content | string | New text |
| important_keywords | array\<string\> | Replaces keyword list |
| available | boolean | `false` skips chunk in retrieval |

---

## 11. Delete chunks — `rm_chunk`

**Description:** Deletes chunks by id in batch.

**Method:** `DELETE`  
**URL:** `/api/v1/datasets/<dataset_id>/documents/<document_id>/chunks`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| chunk_ids | array\<string\> | yes | Chunk ids |

---

## 12. Metadata summary — `metadata_summary`

**Description:** Aggregate stats for the dataset: doc counts, tokens, type and status histograms, custom metadata keys.

**Method:** `GET`  
**URL:** `/api/v1/datasets/<dataset_id>/metadata/summary`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "summary": {
      "total_doc_count": 120,
      "total_token_count": 500000,
      "file_type_distribution": { "pdf": 80, "docx": 30, "txt": 10 },
      "status_distribution": { "1": 118, "0": 2 },
      "custom_metadata": {
        "author": { "Alice": 50, "Bob": 30 },
        "department": { "HR": 20, "Engineering": 100 }
      }
    }
  }
}
```

---

## 13. Batch metadata update — `metadata_batch_update`

**Description:** Bulk upsert or remove metadata keys on documents matched by selector.

**Method:** `POST`  
**URL:** `/api/v1/datasets/<dataset_id>/metadata/update`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| selector | object | no | Scope: `document_ids`, `metadata_condition`; omitting may affect all docs — confirm server behavior |
| updates | array | no | `{ "key", "value" }` rows |
| deletes | array | no | `{ "key" }` rows |

**Example:**

```json
{
  "selector": {
    "document_ids": ["doc_id_101", "doc_id_102"],
    "metadata_condition": {
       "logic": "and",
       "conditions": [
          {"key": "author", "value": "OldName", "operator": "eq"}
       ]
    }
  },
  "updates": [
    {"key": "author", "value": "Admin"},
    {"key": "reviewed_by", "value": "ManagerA"}
  ],
  "deletes": [
    {"key": "temp_tag"}
  ]
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "updated": 2,
    "matched_docs": 2
  }
}
```

---

## 14. Retrieval test — `retrieval_test`

**Description:** Runs retrieval across one or more datasets without the full chat UI — tune thresholds, weights, reranker, and highlighting.

**Method:** `POST`  
**URL:** `/api/v1/retrieval`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| dataset_ids | array\<string\> | yes | — | Datasets to search |
| question | string | yes | — | Query |
| similarity_threshold | float | no | 0.2 | Min score |
| vector_similarity_weight | float | no | 0.3 | Vector share in hybrid scoring |
| top_k | int | no | 1024 | Candidate pool size |
| rerank_id | string | no | — | Reranker model id |
| highlight | boolean | no | true | HTML highlight in snippets |
| keyword | boolean | no | false | LLM keyword expansion |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 15,
    "chunks": [
      {
        "id": "e457f92e3c0411ef8d4c0242ac120003_12",
        "content": "DeepDOC mode handles tables and scanned PDFs...",
        "document_id": "doc_uuid_123",
        "dataset_id": "kb_uuid_456",
        "document_name": "RAGFlow_UserGuide_v2.pdf",
        "document_keyword": "RAGFlow_UserGuide_v2.pdf",
        "similarity": 0.88,
        "vector_similarity": 0.85,
        "term_similarity": 0.92,
        "index": 12,
        "highlight": "DeepDOC mode handles <em>tables</em>...",
        "important_keywords": ["DeepDOC", "PDF"],
        "questions": [],
        "image_id": "",
        "positions": [12]
      }
    ],
    "doc_aggs": [
        { "doc_name": "RAGFlow_UserGuide_v2.pdf", "doc_id": "doc_uuid_123", "count": 1 }
    ]
  }
}
```
