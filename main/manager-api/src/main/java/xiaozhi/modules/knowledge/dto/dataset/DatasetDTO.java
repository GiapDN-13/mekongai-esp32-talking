package xiaozhi.modules.knowledge.dto.dataset;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Knowledge base management aggregate DTO.
 * <p>
 * Container for static nested request/response types used by the knowledge module.
 * </p>
 */
@Schema(description = "Knowledge Base Management Aggregation DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class DatasetDTO {

    // ========== Generic inner classes ==========

    /**
     * Parser configuration.
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Parser configuration")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ParserConfig implements Serializable {

        @Schema(description = "Number of chunked tokens", example = "128")
        @JsonProperty("chunk_token_num")
        private Integer chunkTokenNum;

        @Schema(description = "Delimiter characters for chunking", example = "\\n!?;")
        private String delimiter;

        @Schema(description = "Layout recognition model: DeepDOC / Simple", example = "DeepDOC")
        @JsonProperty("layout_recognize")
        private String layoutRecognize;

        @Schema(description = "Whether to convert Excel to HTML", example = "false")
        private Boolean html4excel;

        @Schema(description = "Number of automatically generated keywords (0 means off)", example = "0")
        @JsonProperty("auto_keywords")
        private Integer autoKeywords;

        @Schema(description = "Number of automatically generated questions (0 means off)", example = "0")
        @JsonProperty("auto_questions")
        private Integer autoQuestions;
    }

    // ========== Request class ==========

    /**
     * Create knowledge base request (maps to create API).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Create a knowledge base request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class CreateReq implements Serializable {

        @NotBlank(message = "Name is required")
        @Schema(description = "Knowledge base name", requiredMode = Schema.RequiredMode.REQUIRED, example = "my_dataset")
        private String name;

        @Schema(description = "Knowledge base avatar (Base64 encoded)", example = "")
        private String avatar;

        @Schema(description = "Knowledge base description", example = "Used to store product documentation")
        private String description;

        @Schema(description = "Embed model name", example = "BAAI/bge-large-zh-v1.5")
        @JsonProperty("embedding_model")
        private String embeddingModel;

        @Schema(description = "Permission settings: me / team", example = "me")
        private String permission;

        @Schema(description = "Chunking method: naive / manual / qa / table / paper / book / laws / presentation / picture / one / knowledge_graph / email", example = "naive")
        @JsonProperty("chunk_method")
        private String chunkMethod;

        @Schema(description = "Parser configuration")
        @JsonProperty("parser_config")
        private ParserConfig parserConfig;
    }

    /**
     * Update knowledge base request (maps to update API).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Update knowledge base request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UpdateReq implements Serializable {

        @Schema(description = "Knowledge base name", example = "updated_dataset")
        private String name;

        @Schema(description = "Knowledge base avatar (Base64 encoded)", example = "")
        private String avatar;

        @Schema(description = "Knowledge base description", example = "Updated description")
        private String description;

        @Schema(description = "Permission settings: me / team", example = "team")
        private String permission;

        @Schema(description = "Embed model name", example = "BAAI/bge-large-zh-v1.5")
        @JsonProperty("embedding_model")
        private String embeddingModel;

        @Schema(description = "Chunking method: naive / manual / qa / table / paper / book / laws / presentation / picture / one / knowledge_graph / email", example = "naive")
        @JsonProperty("chunk_method")
        private String chunkMethod;

        @Schema(description = "Parser configuration")
        @JsonProperty("parser_config")
        private ParserConfig parserConfig;

        @Schema(description = "PageRank weight (0-100)", example = "50")
        private Integer pagerank;
    }

    /**
     * List knowledge bases request (maps to list_datasets API).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Query Knowledge Base List Request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListReq implements Serializable {

        @Schema(description = "Page number (starting from 1)", example = "1")
        private Integer page;

        @Schema(description = "Quantity per page", example = "30")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Sorting fields: create_time / update_time", example = "create_time")
        private String orderby;

        @Schema(description = "Is descending order", example = "true")
        private Boolean desc;

        @Schema(description = "Filter by name (fuzzy match)", example = "my_dataset")
        private String name;

        @Schema(description = "Filter by knowledge base ID", example = "abc123")
        private String id;
    }

    /**
     * Batch delete knowledge bases request (maps to delete API).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Batch delete knowledge base requests")
    public static class BatchIdReq implements Serializable {

        @NotNull(message = "Dataset id list is required")
        @Size(min = 1, message = "At least one dataset id")
        @Schema(description = "Knowledge base ID list", requiredMode = Schema.RequiredMode.REQUIRED, example = "[\"id1\", \"id2\"]")
        private List<String> ids;
    }

    /**
     * Run GraphRAG request body.
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Run a GraphRAG request")
    public static class RunGraphRagReq implements Serializable {

        @Schema(description = "Entity type list", example = "[\"person\", \"organization\"]")
        @JsonProperty("entity_types")
        private List<String> entityTypes;

        @Schema(description = "Build method: light / fast / full", example = "light")
        private String method;
    }

    /**
     * Run RAPTOR request body.
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Run a RAPTOR request")
    public static class RunRaptorReq implements Serializable {

        @Schema(description = "Maximum number of clusters", example = "64")
        @JsonProperty("max_cluster")
        private Integer maxCluster;

        @Schema(description = "Custom prompt words", example = "Please summarize the following...")
        private String prompt;
    }

    /**
     * Async task id response (run_graphrag / run_raptor APIs).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Asynchronous task ID response")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TaskIdVO implements Serializable {

        @Schema(description = "GraphRAG task ID", example = "task_uuid_12345678")
        @JsonProperty("graphrag_task_id")
        private String graphragTaskId;

        @Schema(description = "RAPTOR task ID", example = "task_uuid_87654321")
        @JsonProperty("raptor_task_id")
        private String raptorTaskId;
    }

    // ========== Response class ==========

    /**
     * Knowledge base detail view (return item from create/list APIs).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Knowledge Base Details VO")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class InfoVO implements Serializable {

        @Schema(description = "Knowledge Base ID", example = "abc123")
        private String id;

        @Schema(description = "Knowledge base name", example = "my_dataset")
        private String name;

        @Schema(description = "Knowledge base avatar (Base64 encoded)", example = "")
        private String avatar;

        @Schema(description = "Tenant ID", example = "tenant_001")
        @JsonProperty("tenant_id")
        private String tenantId;

        @Schema(description = "Knowledge base description", example = "Used to store product documentation")
        private String description;

        @Schema(description = "Embed model name", example = "BAAI/bge-large-zh-v1.5")
        @JsonProperty("embedding_model")
        private String embeddingModel;

        @Schema(description = "Permission settings: me / team", example = "me")
        private String permission;

        @Schema(description = "Chunking method", example = "naive")
        @JsonProperty("chunk_method")
        private String chunkMethod;

        @Schema(description = "Parser configuration")
        @JsonProperty("parser_config")
        private ParserConfig parserConfig;

        @Schema(description = "Total number of blocks", example = "1024")
        @JsonProperty("chunk_count")
        private Long chunkCount;

        @Schema(description = "Total number of documents", example = "50")
        @JsonProperty("document_count")
        private Long documentCount;

        @Schema(description = "Creation time (timestamp)", example = "1700000000000")
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Update time (timestamp)", example = "1700000001000")
        @JsonProperty("update_time")
        private Long updateTime;

        @Schema(description = "Total number of tokens", example = "102400")
        @JsonProperty("token_num")
        private Long tokenNum;

        @Schema(description = "Creation date (format: yyyy-MM-dd HH:mm:ss)")
        @JsonProperty("create_date")
        private String createDate;

        @Schema(description = "Last updated date (format: yyyy-MM-dd HH:mm:ss)")
        @JsonProperty("update_date")
        private String updateDate;
    }

    /**
     * Batch operation result view.
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Batch operation response VO")
    public static class BatchOperationVO implements Serializable {

        @Schema(description = "Number of successful operations", example = "5")
        @JsonProperty("success_count")
        private Integer successCount;

        @Schema(description = "error list")
        private List<Object> errors;
    }

    // ========== Knowledge graph related ==========

    /**
     * Knowledge graph payload (knowledge_graph API).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Knowledge graph data VO")
    public static class GraphVO implements Serializable {

        @Schema(description = "Graph node list")
        private List<Node> nodes;

        @Schema(description = "Graph edge list")
        private List<Edge> edges;

        @Schema(description = "mind map data")
        @JsonProperty("mind_map")
        private Map<String, Object> mindMap;

        /**
         * Graph node.
         */
        @Data
        @NoArgsConstructor
        @AllArgsConstructor
        @Builder
        @Schema(description = "graph node")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class Node implements Serializable {

            @Schema(description = "Node ID", example = "node_001")
            private String id;

            @Schema(description = "node label", example = "product")
            private String label;

            @Schema(description = "PageRank value", example = "0.85")
            private Double pagerank;

            @Schema(description = "node color", example = "#FF5733")
            private String color;

            @Schema(description = "Node image URL", example = "https://example.com/icon.png")
            private String img;
        }

        /**
         * Graph edge.
         */
        @Data
        @NoArgsConstructor
        @AllArgsConstructor
        @Builder
        @Schema(description = "Graph edges")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class Edge implements Serializable {

            @Schema(description = "Source node ID", example = "node_001")
            private String source;

            @Schema(description = "Target node ID", example = "node_002")
            private String target;

            @Schema(description = "edge weight", example = "0.75")
            private Double weight;

            @Schema(description = "edge label (relationship description)", example = "belong")
            private String label;
        }
    }

    // ========== Async task trace (GraphRAG / RAPTOR) ==========

    /**
     * Async task progress view (task status APIs).
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Asynchronous task tracking VO")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TaskTraceVO implements Serializable {

        @Schema(description = "Task ID", example = "task_001")
        private String id;

        @Schema(description = "Document ID", example = "doc_001")
        @JsonProperty("doc_id")
        private String docId;

        @Schema(description = "Starting page number", example = "1")
        @JsonProperty("from_page")
        private Integer fromPage;

        @Schema(description = "end page number", example = "10")
        @JsonProperty("to_page")
        private Integer toPage;

        @Schema(description = "Progress percentage (0.0 - 1.0)", example = "0.75")
        private Double progress;

        @Schema(description = "progress message", example = "Processing page 5...")
        @JsonProperty("progress_msg")
        private String progressMsg;

        @Schema(description = "Creation time (timestamp)", example = "1700000000000")
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Update time (timestamp)", example = "1700000001000")
        @JsonProperty("update_time")
        private Long updateTime;
    }
}
