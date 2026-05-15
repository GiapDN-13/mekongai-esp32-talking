package xiaozhi.modules.knowledge.dto.agent;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.*;

@Schema(description = "Agent manages aggregated DTOs")
public class AgentDTO {

    // ========== 1. Agent management (CRUD) - Detailed explanation of the corresponding RAGFlow_Agent interface ==========
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Agent creation request")
    public static class CreateReq implements Serializable {
        @Schema(description = "Agent title", requiredMode = Schema.RequiredMode.REQUIRED, example = "My Agent")
        @NotBlank(message = "Agent title is required")
        @JsonProperty("title")
        private String title;

        @Schema(description = "DSL definition (canvas JSON)", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull(message = "DSL is required")
        @JsonProperty("dsl")
        private Map<String, Object> dsl;

        @Schema(description = "describe", example = "This is a test Agent")
        @JsonProperty("description")
        private String description;

        @Schema(description = "Avatar URL", example = "http://example.com/avatar.png")
        @JsonProperty("avatar")
        private String avatar;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Agent update request")
    public static class UpdateReq implements Serializable {
        @Schema(description = "Agent title", example = "Updated Agent")
        @JsonProperty("title")
        private String title;

        @Schema(description = "DSL definition (canvas JSON)")
        @JsonProperty("dsl")
        private Map<String, Object> dsl;

        @Schema(description = "describe")
        @JsonProperty("description")
        private String description;

        @Schema(description = "Avatar URL")
        @JsonProperty("avatar")
        private String avatar;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Agent list request")
    public static class ListReq implements Serializable {
        @Schema(description = "page number", defaultValue = "1")
        @JsonProperty("page")
        @Builder.Default
        private Integer page = 1;

        @Schema(description = "page size", defaultValue = "10")
        @JsonProperty("page_size")
        @Builder.Default
        private Integer pageSize = 10;

        @Schema(description = "sort field", defaultValue = "update_time")
        @JsonProperty("orderby")
        @Builder.Default
        private String orderby = "update_time";

        @Schema(description = "Is descending order", defaultValue = "true")
        @JsonProperty("desc")
        @Builder.Default
        private Boolean desc = true;

        @Schema(description = "Agent ID filtering")
        @JsonProperty("id")
        private String id;

        @Schema(description = "Title fuzzy search")
        @JsonProperty("title")
        private String title;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Agent response object")
    public static class AgentVO implements Serializable {
        @Schema(description = "Agent ID")
        @JsonProperty("id")
        private String id;

        @Schema(description = "title")
        @JsonProperty("title")
        private String title;

        @Schema(description = "describe")
        @JsonProperty("description")
        private String description;

        @Schema(description = "avatar")
        @JsonProperty("avatar")
        private String avatar;

        @Schema(description = "DSL definition")
        @JsonProperty("dsl")
        private Map<String, Object> dsl;

        @Schema(description = "Creator ID")
        @JsonProperty("user_id")
        private String userId;

        @Schema(description = "Canvas classification")
        @JsonProperty("canvas_category")
        private String canvasCategory;

        @Schema(description = "Creation time (timestamp)")
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Update time (timestamp)")
        @JsonProperty("update_time")
        private Long updateTime;
    }

    // ========== 2. Webhook debugging and tracing - corresponding RAGFlow_Agent interface detailed explanation ==========
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Webhook triggers request (dynamic parameters)")
    public static class WebhookTriggerReq implements Serializable {
        @Schema(description = "input variables", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull(message = "Input variables are required")
        @JsonProperty("inputs")
        private Map<String, Object> inputs;

        @Schema(description = "query word", example = "Hello")
        @JsonProperty("query")
        private String query;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Webhook tracking request")
    public static class WebhookTraceReq implements Serializable {
        @Schema(description = "timestamp cursor", example = "1700000000.0")
        @JsonProperty("since_ts")
        private Double sinceTs;

        @Schema(description = "Webhook ID")
        @JsonProperty("webhook_id")
        private String webhookId;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Webhook tracking response")
    public static class WebhookTraceVO implements Serializable {
        @Schema(description = "Webhook ID")
        @JsonProperty("webhook_id")
        private String webhookId;

        @Schema(description = "Is it over?")
        @JsonProperty("finished")
        private Boolean finished;

        @Schema(description = "timestamp cursor for next query")
        @JsonProperty("next_since_ts")
        private Double nextSinceTs;

        @Schema(description = "event list")
        @JsonProperty("events")
        private List<TraceEvent> events;

        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Track event items")
        public static class TraceEvent implements Serializable {
            @Schema(description = "Timestamp")
            @JsonProperty("ts")
            private Double ts;

            @Schema(description = "event type")
            @JsonProperty("event")
            private String event;

            @Schema(description = "event data")
            @JsonProperty("data")
            private Object data;
        }
    }

    // ========== 3. Agent Session (Session) - Detailed explanation of the corresponding RAGFlow_Agent_Dify interface ==========
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Session creation request")
    public static class SessionCreateReq implements Serializable {
        @Schema(description = "User ID")
        @JsonProperty("user_id")
        private String userId;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Session list request")
    public static class SessionListReq implements Serializable {
        @Schema(description = "page number", defaultValue = "1")
        @JsonProperty("page")
        @Builder.Default
        private Integer page = 1;

        @Schema(description = "page size", defaultValue = "10")
        @JsonProperty("page_size")
        @Builder.Default
        private Integer pageSize = 10;

        @Schema(description = "sort field", defaultValue = "create_time")
        @JsonProperty("orderby")
        @Builder.Default
        private String orderby = "create_time";

        @Schema(description = "Is descending order", defaultValue = "true")
        @JsonProperty("desc")
        @Builder.Default
        private Boolean desc = true;

        @Schema(description = "Session ID")
        @JsonProperty("id")
        private String id;

        @Schema(description = "User ID")
        @JsonProperty("user_id")
        private String userId;

        @Schema(description = "Whether to return DSL")
        @JsonProperty("dsl")
        @Builder.Default
        private Boolean dsl = false;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Session batch delete request")
    public static class SessionBatchDeleteReq implements Serializable {
        @Schema(description = "Session ID list", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("ids")
        @NotEmpty(message = "Id list is required")
        private List<String> ids;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Session response object")
    public static class SessionVO implements Serializable {
        @Schema(description = "Session ID")
        @JsonProperty("id")
        private String id;

        @Schema(description = "Agent ID")
        @JsonProperty("agent_id")
        private String agentId;

        @Schema(description = "User ID")
        @JsonProperty("user_id")
        private String userId;

        @Schema(description = "source")
        @JsonProperty("source")
        private String source;

        @Schema(description = "DSL definition")
        @JsonProperty("dsl")
        private Map<String, Object> dsl;

        @Schema(description = "Message list")
        @JsonProperty("messages")
        private List<Map<String, Object>> messages;
    }

    // ========== 4. Agent dialogue (Completion) - Detailed explanation of the corresponding RAGFlow_Agent_Dify interface ==========
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Completion dialog request")
    public static class CompletionReq implements Serializable {
        @Schema(description = "Session ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Session id is required")
        @JsonProperty("session_id")
        private String sessionId;

        @Schema(description = "User issues")
        @JsonProperty("question")
        private String question;

        @Schema(description = "Whether to stream the return", defaultValue = "true")
        @JsonProperty("stream")
        @Builder.Default
        private Boolean stream = true;

        @Schema(description = "Whether to return tracking information", defaultValue = "false")
        @JsonProperty("return_trace")
        @Builder.Default
        private Boolean returnTrace = false;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Completion dialog response")
    public static class CompletionVO implements Serializable {
        @Schema(description = "Session ID")
        @JsonProperty("id")
        private String id;

        @Schema(description = "Reply content")
        @JsonProperty("content")
        private String content;

        @Schema(description = "Citing sources")
        @JsonProperty("reference")
        private Map<String, Object> reference;

        @Schema(description = "Tracking information")
        @JsonProperty("trace")
        private List<Object> trace;
    }

    // ========== 5. Dify compatible search - corresponding RAGFlow_Agent_Dify interface detailed explanation ==========
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Dify compatible retrieval request")
    public static class DifyRetrievalReq implements Serializable {
        @Schema(description = "Knowledge Base ID")
        @JsonProperty("knowledge_id")
        private String knowledgeId;

        @Schema(description = "query word")
        @JsonProperty("query")
        private String query;

        @Schema(description = "Retrieve settings")
        @JsonProperty("retrieval_setting")
        private Map<String, Object> retrievalSetting;

        @Schema(description = "Metadata filters")
        @JsonProperty("metadata_condition")
        private Map<String, Object> metadataCondition;

        @Schema(description = "Whether to use knowledge graph")
        @JsonProperty("use_kg")
        private Boolean useKg;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Dify compatible retrieval response")
    public static class DifyRetrievalVO implements Serializable {
        @Schema(description = "Search result list")
        @JsonProperty("records")
        private List<Record> records;

        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Retrieve records")
        public static class Record implements Serializable {
            @Schema(description = "content")
            @JsonProperty("content")
            private String content;

            @Schema(description = "similarity score")
            @JsonProperty("score")
            private Double score;

            @Schema(description = "title")
            @JsonProperty("title")
            private String title;

            @Schema(description = "Metadata")
            @JsonProperty("metadata")
            private Map<String, Object> metadata;
        }
    }
}
