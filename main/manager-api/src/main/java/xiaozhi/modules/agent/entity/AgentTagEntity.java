package xiaozhi.modules.agent.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_agent_tag")
@Schema(description = "Agent tag")
public class AgentTagEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Tag id")
    private String id;

    @Schema(description = "Tag name")
    private String tagName;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Creator user id")
    private Long creator;

    @Schema(description = "Created at")
    private Date createdAt;

    @Schema(description = "Last updater user id")
    private Long updater;

    @Schema(description = "Updated at")
    private Date updatedAt;

    @Schema(description = "Soft-delete flag")
    private Integer deleted;
}
