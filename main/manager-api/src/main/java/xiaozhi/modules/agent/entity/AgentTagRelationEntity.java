package xiaozhi.modules.agent.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_agent_tag_relation")
@Schema(description = "Agent–tag link")
public class AgentTagRelationEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Relation id")
    private String id;

    @Schema(description = "Agent id")
    private String agentId;

    @Schema(description = "Tag id")
    private String tagId;

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
}
