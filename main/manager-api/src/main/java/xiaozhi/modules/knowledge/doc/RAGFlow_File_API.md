# RAGFlow file management APIs

## 1. Upload — `upload`

**Description:** Uploads one or more files into a folder. Multipart upload; objects live in MinIO/S3. Returns file metadata per uploaded object.

**Method:** `POST`  
**URL:** `/api/v1/file/upload`  
**Auth:** Header `Authorization: Bearer <API_KEY>`  
**Content-Type:** `multipart/form-data`

### Form fields

| Field | Type | Required | Description |
|---|---|---|---|
| file | file | yes | Binary file(s); multiple files allowed |
| parent_id | string | no | Parent folder id; omit for tenant root |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "e457f92e3c0411ef8d4c0242ac120003",
      "parent_id": "root_folder_id_123",
      "tenant_id": "tenant_uuid_456",
      "created_by": "user_uuid_789",
      "type": "pdf",
      "name": "ProjectReport.pdf",
      "location": "ProjectReport.pdf",
      "size": 204800,
      "source_type": "",
      "create_time": 1715623400123,
      "create_date": "2024-05-13 10:03:20",
      "update_time": 1715623400123,
      "update_date": "2024-05-13 10:03:20"
    }
  ]
}
```

---

## 2. Create folder — `create`

**Description:** Creates a logical folder under a parent.

**Method:** `POST`  
**URL:** `/api/v1/file/create`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| name | string | yes | Folder name (unique among siblings) |
| parent_id | string | no | Parent folder id; root if omitted |
| type | string | yes | Must be `FOLDER` |

**Example:**

```json
{
  "name": "Year2024_Reports",
  "parent_id": "root_folder_id_123",
  "type": "FOLDER"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "folder_uuid_abc",
    "parent_id": "root_folder_id_123",
    "tenant_id": "tenant_uuid_456",
    "created_by": "user_uuid_789",
    "name": "Year2024_Reports",
    "location": "",
    "size": 0,
    "type": "folder",
    "source_type": "",
    "create_time": 1715623500000,
    "create_date": "2024-05-13 10:05:00",
    "update_time": 1715623500000,
    "update_date": "2024-05-13 10:05:00"
  }
}
```

---

## 3. List files — `list_files`

**Description:** Paged listing of files and subfolders; optional name keyword search.

**Method:** `GET`  
**URL:** `/api/v1/file/list`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| parent_id | string | no | Root | Folder to list |
| keywords | string | no | — | Fuzzy file name |
| page | int | no | 1 | Page |
| page_size | int | no | 15 | Page size |
| orderby | string | no | `"create_time"` | Sort field |
| desc | boolean | no | true | Descending |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 25,
    "parent_folder": { },
    "files": [ ]
  }
}
```

---

## 4. Download file by id — `get`

**Description:** Streams raw bytes for a stored file id (not JSON metadata).

**Method:** `GET`  
**URL:** `/api/v1/file/get/<file_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

**Content-Type:** `application/octet-stream` or specific MIME (e.g. `image/png`).

---

## 5. Download attachment — `download_attachment`

**Description:** Generic attachment download by storage key / attachment id (often MinIO object key).

**Method:** `GET`  
**URL:** `/api/v1/file/download/<attachment_id>`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| ext | string | no | `"markdown"` | Hint for `Content-Type` |

### Response

Binary stream.

---

## 6. Rename — `rename`

**Description:** Renames a file or folder. File extension usually must stay consistent with the stored type.

**Method:** `POST`  
**URL:** `/api/v1/file/rename`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| file_id | string | yes | File or folder id |
| name | string | yes | New name (unique among siblings) |

### Response

```json
{ "code": 0, "message": "success", "data": true }
```

---

## 7. Move — `move`

**Description:** Moves files/folders to another folder.

**Method:** `POST`  
**URL:** `/api/v1/file/mv`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| src_file_ids | array\<string\> | yes | Items to move |
| dest_file_id | string | yes | Target folder id |

### Response

```json
{ "code": 0, "message": "success", "data": true }
```

---

## 8. Remove — `rm`

**Description:** Deletes files/folders by id. Folders are removed recursively (**irreversible**).

**Method:** `POST`  
**URL:** `/api/v1/file/rm`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| file_ids | array\<string\> | yes | Ids to delete |

### Response

```json
{ "code": 0, "message": "success", "data": true }
```

---

## 9. Import file into dataset — `convert`

**Description:** Turns stored **files** into **documents** inside one or more datasets and kicks off parsing.

**Method:** `POST`  
**URL:** `/api/v1/file/convert`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Body (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| file_ids | array\<string\> | yes | Existing file ids |
| kb_ids | array\<string\> | yes | Target dataset ids |

### Response

Array of `{ file_id, document_id, ... }` mapping rows.

---

## 10. Root folder — `get_root_folder`

**Description:** Returns the tenant user’s single root folder record.

**Method:** `GET`  
**URL:** `/api/v1/file/root_folder`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "root_folder": { }
  }
}
```

---

## 11. Parent folder — `get_parent_folder`

**Description:** Direct parent folder of a file or folder id.

**Method:** `GET`  
**URL:** `/api/v1/file/parent_folder`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Description |
|---|---|---|---|
| file_id | string | yes | File or folder id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": { "parent_folder": { } }
}
```

---

## 12. Breadcrumb path — `get_all_parent_folders`

**Description:** Ordered list of ancestors from root to direct parent (breadcrumbs).

**Method:** `GET`  
**URL:** `/api/v1/file/all_parent_folder`  
**Auth:** Header `Authorization: Bearer <API_KEY>`

### Query parameters

| Field | Type | Required | Description |
|---|---|---|---|
| file_id | string | yes | File or folder id |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "parent_folders": [ ]
  }
}
```
