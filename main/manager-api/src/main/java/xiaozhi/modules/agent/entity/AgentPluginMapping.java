package xiaozhi.modules.agent.entity;

import java.io.Serializable;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * One agent–plugin mapping row ({@code ai_agent_plugin_mapping}).
 *
 * @TableName ai_agent_plugin_mapping
 */
@Data
@TableName(value = "ai_agent_plugin_mapping")
@Schema(description = "Agent plugin mapping")
public class AgentPluginMapping implements Serializable {
    /**
     * Surrogate key.
     */
    @TableId(type = IdType.ASSIGN_ID)
    @Schema(description = "Mapping row id")
    private Long id;

    /**
     * Agent id.
     */
    @Schema(description = "Agent id")
    private String agentId;

    /**
     * Plugin id.
     */
    @Schema(description = "Plugin id")
    private String pluginId;

    /**
     * Plugin parameters (JSON).
     */
    @Schema(description = "Plugin parameters (JSON)")
    private String paramInfo;

    /** Denormalized provider code for joins; see mapper XML. */
    @TableField(exist = false)
    @Schema(description = "Provider code (ai_model_provider)")
    private String providerCode;

    @TableField(exist = false)
    private static final long serialVersionUID = 1L;
}