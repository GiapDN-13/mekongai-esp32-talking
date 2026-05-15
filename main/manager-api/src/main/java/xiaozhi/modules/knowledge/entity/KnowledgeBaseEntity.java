package xiaozhi.modules.knowledge.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName(value = "ai_rag_dataset", autoResultMap = true)
@Schema(description = "Knowledge base (dataset)")
public class KnowledgeBaseEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Primary key")
    private String id;

    @Schema(description = "RAG dataset id")
    private String datasetId;

    @Schema(description = "RAG model config id (credentials pointer)")
    private String ragModelId;

    @Schema(description = "Tenant id")
    private String tenantId;

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

    @Schema(description = "Chunk method key")
    private String chunkMethod;

    @Schema(description = "Parser config JSON string")
    private String parserConfig;

    @Schema(description = "Total chunk count")
    private Long chunkCount;

    @Schema(description = "Document count")
    private Long documentCount;

    @Schema(description = "Total token count")
    private Long tokenNum;

    @Schema(description = "Status: 0 disabled, 1 enabled")
    private Integer status;

    @Schema(description = "Creator user id")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Created at")
    @TableField(fill = FieldFill.INSERT)
    private Date createdAt;

    @Schema(description = "Last updater user id")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Updated at")
    @TableField(fill = FieldFill.UPDATE)
    private Date updatedAt;
}
