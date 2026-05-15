package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Document management aggregate DTO (nested request/response types).
 */
@Schema(description = "Document Management Aggregation DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class DocumentDTO {

    /**
     * Upload document request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Upload document request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UploadReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Knowledge base ID (required to specify attribution)", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_id")
        @NotBlank(message = "Dataset id is required")
        private String datasetId;

        @Schema(description = "filename (if specified, overwrites the original filename)")
        private String name;

        @Schema(description = "Chunking method")
        @JsonProperty("chunk_method")
        private DocumentDTO.InfoVO.ChunkMethod chunkMethod;

        @Schema(description = "Parse parameter configuration")
        @JsonProperty("parser_config")
        private DocumentDTO.InfoVO.ParserConfig parserConfig;

        @Schema(description = "Virtual folder path (default is /)")
        @JsonProperty("parent_path")
        private String parentPath;

        @Schema(description = "metadata fields")
        @JsonProperty("meta")
        private Map<String, Object> metaFields;

        @Schema(description = "File binary stream (supports PDF, DOCX, TXT, MD and other formats)", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull(message = "Upload file is required")
        private org.springframework.web.multipart.MultipartFile file;
    }

    /**
     * Update document request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Update document request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UpdateReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "New document name (must include file suffix and cannot change original type)")
        private String name;

        @Schema(description = "Enable/disable status (true: enabled, false: disabled; will not participate in retrieval after being disabled)")
        private Boolean enabled;

        @Schema(description = "New parsing method (modifying this will reset the parsing status)")
        @JsonProperty("chunk_method")
        private InfoVO.ChunkMethod chunkMethod;

        @Schema(description = "Detailed configuration of the new parser (should be used with chunk_method)")
        @JsonProperty("parser_config")
        private InfoVO.ParserConfig parserConfig;
    }

    /**
     * List documents request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Get document list request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Page number (default: 1)")
        private Integer page;

        @Schema(description = "Number per page (default: 30)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Sorting field (optional: create_time, name, size; default: create_time)")
        private String orderby;

        @Schema(description = "Whether to sort in descending order (true: newest/largest first; false: oldest/smallest first; default: true)")
        private Boolean desc;

        @Schema(description = "Refine filter: Document ID")
        private String id;

        @Schema(description = "Exact filtering: Full document name (including suffix)")
        private String name;

        @Schema(description = "Fuzzy search: document name keywords")
        private String keywords;

        @Schema(description = "Filter: file suffix list (e.g. ['pdf', 'docx'])")
        private List<String> suffix;

        @Schema(description = "Filter: Running status list")
        private List<InfoVO.RunStatus> run;

        @Schema(description = "Filter: Start creation time (timestamp, milliseconds)")
        @JsonProperty("create_time_from")
        private Long createTimeFrom;

        @Schema(description = "Filter: end creation time (timestamp, milliseconds)")
        @JsonProperty("create_time_to")
        private Long createTimeTo;
    }

    /**
     * Batch document operation request (delete, parse, etc.).
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Batch document operation request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BatchIdReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document ID list", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("ids") // Accepts "ids"; document_ids is supported via @JsonAlias
        @JsonAlias("document_ids")
        @NotEmpty(message = "Document ids are required")
        private List<String> ids;
    }

    /**
     * Knowledge base document detail view.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Knowledge base document information")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class InfoVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document ID (unique identifier)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Document thumbnail URL (Base64 or link)")
        private String thumbnail;

        @Schema(description = "Knowledge base ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Document parsing method (determines how the document is sliced)")
        @JsonProperty("chunk_method")
        private ChunkMethod chunkMethod;

        @Schema(description = "Associated ETL Pipeline ID (if any)")
        @JsonProperty("pipeline_id")
        private String pipelineId;

        @Schema(description = "Detailed configuration of document parser")
        @JsonProperty("parser_config")
        private ParserConfig parserConfig;

        @Schema(description = "Source type (such as local, s3, url, etc.)")
        @JsonProperty("source_type")
        private String sourceType;

        @Schema(description = "Document file type (e.g. pdf, docx, txt)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String type;

        @Schema(description = "Creator user ID")
        @JsonProperty("created_by")
        private String createdBy;

        @Schema(description = "Document name (including extension)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String name;

        @Schema(description = "File storage path or location identifier")
        private String location;

        @Schema(description = "File size (unit: Bytes)")
        private Long size;

        @Schema(description = "Total number of tokens included (statistics after parsing)")
        @JsonProperty("token_count")
        private Long tokenCount;

        @Schema(description = "The total number of slices (Chunks) contained")
        @JsonProperty("chunk_count")
        private Long chunkCount;

        @Schema(description = "Parsing progress (0.0 ~ 1.0, 1.0 indicates completion)")
        private Double progress;

        @Schema(description = "Current progress description or error information")
        @JsonProperty("progress_msg")
        private String progressMsg;

        @Schema(description = "Timestamp when processing started (RAGFlow returns RFC1123 format)")
        @JsonProperty("process_begin_at")
        private String processBeginAt;

        @Schema(description = "Total processing time (unit: seconds)")
        @JsonProperty("process_duration")
        private Double processDuration;

        @Schema(description = "Custom metadata fields (Key-Value pairs)")
        @JsonProperty("meta_fields")
        private Map<String, Object> metaFields;

        @Schema(description = "File extension (without dot)")
        private String suffix;

        @Schema(description = "Document parsing running status")
        private RunStatus run;

        @Schema(description = "Document availability status (1: enabled/normal, 0: disabled/invalid)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String status;

        @Schema(description = "Creation time (timestamp, milliseconds)", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Creation date (RAGFlow returns RFC1123 format)")
        @JsonProperty("create_date")
        private String createDate;

        @Schema(description = "Last updated time (timestamp, milliseconds)")
        @JsonProperty("update_time")
        private Long updateTime;

        @Schema(description = "Last updated date (RAGFlow returns RFC1123 format)")
        @JsonProperty("update_date")
        private String updateDate;

        /**
         * Chunking / parsing strategy (ChunkMethod).
         */
        public enum ChunkMethod {
            @Schema(description = "Universal mode: suitable for most plain text or mixed documents")
            @JsonProperty("naive")
            NAIVE,
            @Schema(description = "Manual mode: allows the user to edit slices manually")
            @JsonProperty("manual")
            MANUAL,
            @Schema(description = "Q&A mode: Documents specially optimized for Q&A format")
            @JsonProperty("qa")
            QA,
            @Schema(description = "Table mode: specifically optimized for table data such as Excel or CSV")
            @JsonProperty("table")
            TABLE,
            @Schema(description = "Paper Mode: Optimized for academic paper formatting")
            @JsonProperty("paper")
            PAPER,
            @Schema(description = "Book Mode: Optimized for book chapter structure")
            @JsonProperty("book")
            BOOK,
            @Schema(description = "Legal and regulatory model: Optimizing the structure of legal provisions")
            @JsonProperty("laws")
            LAWS,
            @Schema(description = "Presentation mode: Optimized for presentation files such as PPT")
            @JsonProperty("presentation")
            PRESENTATION,
            @Schema(description = "Image mode: OCR and describe image content")
            @JsonProperty("picture")
            PICTURE,
            @Schema(description = "Whole mode: Treat the entire document as a slice")
            @JsonProperty("one")
            ONE,
            @Schema(description = "Knowledge graph mode: extract entity relationships to build a graph")
            @JsonProperty("knowledge_graph")
            KNOWLEDGE_GRAPH,
            @Schema(description = "Email Mode: Optimized for email formats")
            @JsonProperty("email")
            EMAIL;
        }

        /**
         * Document parsing pipeline status (RunStatus).
         */
        public enum RunStatus {
            @Schema(description = "Not started: waiting for parsing queue")
            @JsonProperty("UNSTART")
            UNSTART,
            @Schema(description = "In Progress: Parsing or indexing")
            @JsonProperty("RUNNING")
            RUNNING,
            @Schema(description = "Canceled: Manually canceled by user")
            @JsonProperty("CANCEL")
            CANCEL,
            @Schema(description = "Completed: Parsing successful")
            @JsonProperty("DONE")
            DONE,
            @Schema(description = "Failure: Error during parsing")
            @JsonProperty("FAIL")
            FAIL;
        }

        /**
         * Layout recognition model option.
         */
        public enum LayoutRecognize {
            @Schema(description = "Deep document understanding model: suitable for complex typesetting")
            @JsonProperty("DeepDOC")
            DeepDOC,
            @Schema(description = "Simple rule model: suitable for plain text")
            @JsonProperty("Simple")
            Simple;
        }

        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Document parser parameter configuration")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class ParserConfig implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Maximum number of Tokens in a slice (recommended values: 512, 1024, 2048)")
            @JsonProperty("chunk_token_num")
            private Integer chunkTokenNum;

            @Schema(description = "Paragraph delimiter (supports escape characters, such as \\n)")
            private String delimiter;

            @Schema(description = "Layout recognition model (DeepDOC/Simple)")
            @JsonProperty("layout_recognize")
            private LayoutRecognize layoutRecognize;

            @Schema(description = "Whether to convert Excel to HTML table")
            @JsonProperty("html4excel")
            private Boolean html4excel;

            @Schema(description = "Number of keywords automatically extracted (0 means no extraction)")
            @JsonProperty("auto_keywords")
            private Integer autoKeywords;

            @Schema(description = "Number of automatically generated questions (0 means no generation)")
            @JsonProperty("auto_questions")
            private Integer autoQuestions;

            @Schema(description = "Automatically generate label quantity")
            @JsonProperty("topn_tags")
            private Integer topnTags;

            @Schema(description = "RAPTOR advanced index configuration")
            private RaptorConfig raptor;

            @Schema(description = "GraphRAG knowledge graph configuration")
            @JsonProperty("graphrag")
            private GraphRagConfig graphRag;

            @Data
            @Builder
            @NoArgsConstructor
            @AllArgsConstructor
            @Schema(description = "RAPTOR (Recursive Abstract Index) configuration")
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class RaptorConfig implements Serializable {
                private static final long serialVersionUID = 1L;
                @Schema(description = "Whether to enable RAPTOR indexing")
                @JsonProperty("use_raptor")
                private Boolean useRaptor;
            }

            @Data
            @Builder
            @NoArgsConstructor
            @AllArgsConstructor
            @Schema(description = "GraphRAG (graph enhanced retrieval) configuration")
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class GraphRagConfig implements Serializable {
                private static final long serialVersionUID = 1L;
                @Schema(description = "Whether to enable GraphRAG indexing")
                @JsonProperty("use_graphrag")
                private Boolean useGraphRag;
            }
        }
    }
}
