package xiaozhi.modules.agent.vo;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.modules.agent.dto.ContextProviderDTO;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.entity.AgentPluginMapping;

import java.util.List;

/**
 * Agent detail response; extends {@link AgentEntity} with relations.
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class AgentInfoVO extends AgentEntity
{
    @Schema(description = "Plugin mappings")
    @TableField(typeHandler = JacksonTypeHandler.class)
    private List<AgentPluginMapping> functions;

    @Schema(description = "Context providers")
    private List<ContextProviderDTO> contextProviders;
}
