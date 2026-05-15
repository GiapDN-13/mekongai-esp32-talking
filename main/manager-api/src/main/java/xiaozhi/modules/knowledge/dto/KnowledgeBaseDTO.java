package xiaozhi.modules.knowledge.dto;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "Knowledge base")
public class KnowledgeBaseDTO implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Schema(description = "Primary key")
    private String id;

    @Schema(description = "RAG dataset id")
    private String datasetId;

    @Schema(description = "RAG model config id")
    private String ragModelId;

    @Schema(description = "Display name")
    private String name;

    @Schema(description = "Avatar (Base64)")
    private String avatar;

    @Schema(description = "Description")
    private String description;

    @Schema(description = "Embedding model name")
    private String embeddingModel;

    @Schema(description = "Permission: me / team")
    private String permission;

    @Schema(description = "Chunk method")
    private String chunkMethod;

    @Schema(description = "Parser config JSON string")
    private String parserConfig;

    @Schema(description = "Total chunk count")
    private Long chunkCount;

    @Schema(description = "Total token count")
    private Long tokenNum;

    @Schema(description = "Status: 0 disabled, 1 enabled")
    private Integer status;

    @Schema(description = "Creator user id")
    private Long creator;

    @Schema(description = "Created at")
    private Date createdAt;

    @Schema(description = "Last updater user id")
    private Long updater;

    @Schema(description = "Updated at")
    private Date updatedAt;

    @Schema(description = "Document count")
    private Integer documentCount;
}
