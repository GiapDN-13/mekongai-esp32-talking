package xiaozhi.modules.knowledge.dto;

import java.io.Serializable;
import java.util.Date;
import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Legacy flat document DTO (admin/list views).
 */
@Data
@Schema(description = "Knowledge base document (flat)")
public class DocumentDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Local row id")
    private String id;

    @Schema(description = "Dataset id")
    private String datasetId;

    @Schema(description = "RAGFlow document id")
    private String documentId;

    @Schema(description = "File name")
    private String name;

    @Schema(description = "File size in bytes")
    private Long size;

    @Schema(description = "File type")
    private String type;

    @Schema(description = "Chunk method")
    private String chunkMethod;

    @Schema(description = "Parser config")
    private Map<String, Object> parserConfig;

    @Schema(description = "Legacy status code (1 parsing, 3 ok, 4 fail)")
    private Integer status;

    @Schema(description = "Error message")
    private String error;

    @Schema(description = "Chunk count")
    private Integer chunkCount;

    @Schema(description = "Token count")
    private Long tokenCount;

    @Schema(description = "Enabled flag")
    private Integer enabled;

    @Schema(description = "Created at")
    private Date createdAt;

    @Schema(description = "Updated at")
    private Date updatedAt;

    @Schema(description = "Upload / parse progress (derived)")
    private Double progress;

    @Schema(description = "Thumbnail (derived)")
    private String thumbnail;
}
