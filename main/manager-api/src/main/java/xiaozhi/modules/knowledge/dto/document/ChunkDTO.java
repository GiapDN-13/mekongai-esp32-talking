package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Chunk management aggregate DTO (nested request/response types).
 */
@Schema(description = "Slice management aggregate DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class ChunkDTO {

    /**
     * Add chunk request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Added slice request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AddReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "slice content", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Chunk text is required")
        private String content;

        @Schema(description = "Important keyword list")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Default question list")
        private List<String> questions;
    }

    /**
     * Update chunk request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Update slice request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UpdateReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "New slice content")
        private String content;

        @Schema(description = "Update keyword list (overwrite original list)")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Enable/disable (true: enable, false: disable)")
        private Boolean available;
    }

    /**
     * List chunks request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Get slice list request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Page number (default 1)")
        private Integer page;

        @Schema(description = "Number per page (default 30)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Search keywords (full text search)")
        private String keywords;

        @Schema(description = "Exact slice ID")
        private String id;
    }

    /**
     * Batch delete chunks request body.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Delete slice request parameters in batches")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class RemoveReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "List of slice IDs", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("chunk_ids")
        @NotEmpty(message = "Chunk ids are required")
        private List<String> chunkIds;
    }

    /**
     * Chunk detail view object.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Document slice information")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class InfoVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Slice ID (usually document_id + index)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Sliced ​​text content (the main object of full-text retrieval)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String content;

        @Schema(description = "Document ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("document_id")
        private String documentId;

        @Schema(description = "Document name/keywords")
        @JsonProperty("docnm_kwd")
        private String docnmKwd;

        @Schema(description = "Important keyword list (for keyword enhanced search)")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Preset question list (for Q&A mode enhancement)")
        private List<String> questions;

        @Schema(description = "Associated image ID")
        @JsonProperty("image_id")
        private String imageId;

        @Schema(description = "Knowledge base ID")
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Whether the slice is available (true: participate in retrieval, false: disabled)")
        private Boolean available;

        @Schema(description = "List of position indexes of the slice in the original text (RAGFlow returns a nested array, such as [[start, end, filename]])")
        private List<List<Object>> positions;

        @Schema(description = "Token ID list")
        @JsonProperty("token")
        private List<Integer> token;
    }

    /**
     * Chunk list response with optional document context.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Sharded list aggregate response")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Slice information list")
        private List<InfoVO> chunks;

        @Schema(description = "Associated document details")
        private DocumentDTO.InfoVO doc;

        @Schema(description = "Total number of records")
        private Long total;
    }
}
