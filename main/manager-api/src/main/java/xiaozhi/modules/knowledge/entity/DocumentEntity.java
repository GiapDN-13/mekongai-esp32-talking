package xiaozhi.modules.knowledge.entity;

import java.io.Serializable;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Shadow row for a RAGFlow document ({@code ai_rag_knowledge_document}).
 */
@Data
@TableName(value = "ai_rag_knowledge_document", autoResultMap = true)
@Schema(description = "Knowledge base document (shadow)")
public class DocumentEntity implements Serializable {
    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Local row id")
    private String id;

    @Schema(description = "Dataset id (ai_rag_dataset.dataset_id)")
    private String datasetId;

    @Schema(description = "RAGFlow document id")
    private String documentId;

    @Schema(description = "File name")
    private String name;

    @Schema(description = "File size in bytes")
    private Long size;

    @Schema(description = "File type (pdf, doc, txt, ...)")
    private String type;

    @Schema(description = "Chunk method")
    private String chunkMethod;

    @Schema(description = "Parser config JSON string")
    private String parserConfig;

    @Schema(description = "Availability: 1 normal, 0 disabled")
    private String status;

    @Schema(description = "Run state: UNSTART / RUNNING / CANCEL / DONE / FAIL")
    private String run;

    @Schema(description = "Parse progress 0.0–1.0")
    private Double progress;

    @Schema(description = "Thumbnail Base64 or URL")
    private String thumbnail;

    @Schema(description = "Parse duration in seconds")
    private Double processDuration;

    @Schema(description = "Custom metadata JSON")
    private String metaFields;

    @Schema(description = "Source type: local, s3, url, ...")
    private String sourceType;

    @Schema(description = "Parse error message")
    private String error;

    @Schema(description = "Chunk count")
    private Integer chunkCount;

    @Schema(description = "Token count")
    private Long tokenCount;

    @Schema(description = "Enabled flag: 0 / 1")
    private Integer enabled;

    @Schema(description = "Creator user id")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Created at")
    @TableField(fill = FieldFill.INSERT)
    private Date createdAt;

    @Schema(description = "Updated at")
    @TableField(fill = FieldFill.UPDATE)
    private Date updatedAt;

    @Schema(description = "Last sync with RAG")
    private Date lastSyncAt;
}
