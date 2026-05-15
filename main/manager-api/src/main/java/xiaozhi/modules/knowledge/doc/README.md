# RAGFlow API documentation index (unofficial)

This folder contains detailed notes on RAGFlow HTTP APIs used by the knowledge module integration. The guides aim for **full field coverage** (no omitted nested fields) with English descriptions.

## 1. Knowledge and documents

- **[Dataset (knowledge base)](./RAGFlow_Dataset_API.md)** — Create, list, update, delete datasets; GraphRAG/RAPTOR; knowledge graph.
- **[Document](./RAGFlow_Document_API.md)** — Upload, update, parse status, download; chunk CRUD; retrieval test; metadata summary and batch update.
- **[File](./RAGFlow_File_API.md)** — File manager style API: upload, download, list, folders, move, rename, delete, import to dataset (`convert`).

## 2. Chat assistant

- **[Chat assistant CRUD](./RAGFlow_Chat_API.md)** — Create/list/update/delete chat apps (dialogs), LLM and prompt configuration.
- **[Chat session](./RAGFlow_Chat_Session_API.md)** — Sessions under `/chats/`: create, history, rename, batch delete.
- **[Chat completion](./RAGFlow_Chat_Completion_API.md)** — Native streaming (`/chats/<id>/completions`), OpenAI-compatible `/v1/chat/completions`, embedded chatbots (`/chatbots/`).

## 3. Agents and bots

- **[Agent & Dify compatibility](./RAGFlow_Agent_Dify_API.md)** — Agent sessions and streaming (`agent_completions`); Dify-style retrieval (`/dify/retrieval`).
- **[SearchBot & AgentBot](./RAGFlow_SearchBot_AgentBot_API.md)** — SearchBot (mind map, related questions); AgentBot (begin inputs); Agent OpenAI-compatible chat.

## 4. Agents (CRUD and webhooks)

- **[Agent](./RAGFlow_Agent_API.md)** — List/create/update/delete agents; webhook test and trace.

## 5. Extras

- **[Session extras](./RAGFlow_Session_Extra_API.md)** — SearchBot citation detail (`detail_share_embedded`); generic ask (`ask_about`).

## 6. Reference tables

- **[API classification (external vs internal)](./RAGFlow_API_classification_table.md)** — Maps SDK Python entry points to `/api/v1/...` routes.
- **[External APIs by source file](./RAGFlow_external_API_list_by_source_file.md)** — Same routes grouped by `api/apps/sdk/*.py` file.

These documents describe upstream RAGFlow behavior; path prefixes and payloads should be verified against your deployed RAGFlow version.

## Note on `RAGFlow_Document_API.md` (English)

The English **Document** guide is **shorter than the former Chinese version**: long repeated JSON examples were trimmed in favor of the same field descriptions used elsewhere. Restore or expand examples from git history if you need line-by-line parity with the old doc.
