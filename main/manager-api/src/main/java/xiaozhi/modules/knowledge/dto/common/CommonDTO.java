package xiaozhi.modules.knowledge.dto.common;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.*;

@Schema(description = "General extended function DTO")
public class CommonDTO {

    // ========== 1. Quote details (detail_share_embedded) ==========

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Reference details request")
    public static class ReferenceDetailReq implements Serializable {
        @Schema(description = "Slice ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Chunk id is required")
        @JsonProperty("chunk_id")
        private String chunkId;

        @Schema(description = "Knowledge Base ID")
        @JsonProperty("knowledge_id")
        private String knowledgeId;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Quote details response")
    public static class ReferenceDetailVO implements Serializable {
        @Schema(description = "Slice ID")
        @JsonProperty("chunk_id")
        private String chunkId;

        @Schema(description = "full content")
        @JsonProperty("content_with_weight")
        private String contentWithWeight;

        @Schema(description = "file name")
        @JsonProperty("doc_name")
        private String docName;

        @Schema(description = "Image ID list")
        @JsonProperty("img_id")
        /** RAGFlow may return string or list; we store a single id string when possible. */
        private String imageId;

        @Schema(description = "Document ID")
        @JsonProperty("doc_id")
        private String docId;
    }

    // ========== 2. General Q&A (ask_about) - for debugging ==========

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "General Q&A requests (for debugging)")
    public static class AskAboutReq implements Serializable {
        @Schema(description = "User issues", requiredMode = Schema.RequiredMode.REQUIRED, example = "What is this dataset about?")
        @NotBlank(message = "Question is required")
        @JsonProperty("question")
        private String question;

        @Schema(description = "List of dataset IDs", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotEmpty(message = "Dataset list is required")
        @JsonProperty("dataset_ids")
        private List<String> datasetIds;
    }

    // The response usually reuses String or simple Map structure, depending on the specific implementation. No dedicated VO is defined yet.
}
