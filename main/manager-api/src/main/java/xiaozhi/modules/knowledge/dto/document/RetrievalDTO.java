package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Retrieval and metadata management aggregate DTO.
 */
@Schema(description = "Retrieval and metadata management aggregate DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class RetrievalDTO {

    /**
     * Per-document aggregation in retrieval results.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Document aggregation entry")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class DocAggVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document name")
        @JsonProperty("doc_name")
        private String docName;

        @Schema(description = "Document id")
        @JsonProperty("doc_id")
        private String docId;

        @Schema(description = "Hit count for this document")
        private Integer count;
    }

    /**
     * Retrieval test request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Retrieval test request body")
    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class TestReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Knowledge base id list", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_ids")
        @NotEmpty(message = "Dataset ids are required")
        private List<String> datasetIds;

        @Schema(description = "Optional document id list to limit retrieval scope")
        @JsonProperty("document_ids")
        private List<String> documentIds;

        @Schema(description = "Search question", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Question is required")
        private String question;

        @Schema(description = "Page number (default 1)")
        private Integer page;

        @Schema(description = "Page size (default 10)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Similarity threshold (default 0.2)")
        @JsonProperty("similarity_threshold")
        private Float similarityThreshold;

        @Schema(description = "Vector similarity weight (default 0.3)")
        @JsonProperty("vector_similarity_weight")
        private Float vectorSimilarityWeight;

        @Schema(description = "Top-K chunks to return (default 1024)")
        @JsonProperty("top_k")
        private Integer topK;

        @Schema(description = "Rerank model id")
        @JsonProperty("rerank_id")
        private String rerankId;

        @Schema(description = "Whether to highlight keywords in results")
        private Boolean highlight;

        @Schema(description = "Whether to enable keyword (term) retrieval")
        private Boolean keyword;

        @Schema(description = "Cross-language codes (optional)")
        @JsonProperty("cross_languages")
        private List<String> crossLanguages;

        @Schema(description = "Metadata filter object (JSON)")
        @JsonProperty("metadata_condition")
        private Map<String, Object> metadataCondition;
    }

    /**
     * Single retrieval hit (chunk detail).
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Retrieval hit chunk detail")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class HitVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Chunk id", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Chunk text", requiredMode = Schema.RequiredMode.REQUIRED)
        private String content;

        @Schema(description = "Owning document id", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("document_id")
        private String documentId;

        @Schema(description = "Owning knowledge base id")
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Document name")
        @JsonProperty("document_name")
        private String documentName;

        @Schema(description = "Document keyword field")
        @JsonProperty("document_keyword")
        private String documentKeyword;

        @Schema(description = "Combined similarity score", requiredMode = Schema.RequiredMode.REQUIRED)
        private Float similarity;

        @Schema(description = "Vector similarity score")
        @JsonProperty("vector_similarity")
        private Float vectorSimilarity;

        @Schema(description = "Keyword (term) similarity score")
        @JsonProperty("term_similarity")
        private Float termSimilarity;

        @Schema(description = "Result index position")
        private Integer index;

        @Schema(description = "Highlighted snippet HTML or text")
        private String highlight;

        @Schema(description = "Important keywords")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Preset questions")
        private List<String> questions;

        @Schema(description = "Image id")
        @JsonProperty("image_id")
        private String imageId;

        @Schema(description = "Position spans (RAGFlow nested array, e.g. [[start, end, filename]])")
        private Object positions;
    }

    /**
     * Knowledge base metadata summary.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Knowledge base metadata summary")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MetaSummaryVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Total document count", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("total_doc_count")
        private Long totalDocCount;

        @Schema(description = "Total token count", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("total_token_count")
        private Long totalTokenCount;

        @Schema(description = "File type distribution (key: suffix, value: count)")
        @JsonProperty("file_type_distribution")
        private Map<String, Long> fileTypeDistribution;

        @Schema(description = "Document status distribution (key: status code, value: count)")
        @JsonProperty("status_distribution")
        private Map<String, Long> statusDistribution;

        @Schema(description = "Custom metadata stats (key: field name, value: count or value)")
        @JsonProperty("custom_metadata")
        private Map<String, Object> customMetadata;
    }

    /**
     * Batch metadata update request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Batch metadata update request body")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MetaBatchReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Selector for documents to update (default: all)")
        private Selector selector;

        @Schema(description = "Metadata entries to add or update")
        private List<UpdateItem> updates;

        @Schema(description = "Metadata keys to remove")
        private List<DeleteItem> deletes;

        /**
         * Document scope for metadata updates.
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata update selector")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class Selector implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Explicit document id list")
            @JsonProperty("document_ids")
            private List<String> documentIds;

            @Schema(description = "Metadata match filter (key: field name, value: expected value)")
            @JsonProperty("metadata_condition")
            private Map<String, Object> metadataCondition;
        }

        /**
         * Upsert one metadata key-value pair.
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata update entry")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class UpdateItem implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Metadata key", requiredMode = Schema.RequiredMode.REQUIRED)
            private String key;

            @Schema(description = "Metadata value", requiredMode = Schema.RequiredMode.REQUIRED)
            private Object value;
        }

        /**
         * Remove one metadata key.
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata delete entry")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class DeleteItem implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Metadata key to remove", requiredMode = Schema.RequiredMode.REQUIRED)
            private String key;
        }
    }

    /**
     * Aggregated retrieval test response.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Retrieval test aggregated response")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ResultVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Hit chunks")
        private List<HitVO> chunks;

        @Schema(description = "Per-document hit statistics")
        @JsonProperty("doc_aggs")
        private List<DocAggVO> docAggs;

        @Schema(description = "Total number of hits")
        private Long total;
    }
}
