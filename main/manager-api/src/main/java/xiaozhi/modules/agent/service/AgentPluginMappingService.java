package xiaozhi.modules.agent.service;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.IService;

import xiaozhi.modules.agent.entity.AgentPluginMapping;

/**
 * Agent plugin bindings ({@code ai_agent_plugin_mapping}).
 *
 * @createDate 2025-05-25 22:33:17
 */
public interface AgentPluginMappingService extends IService<AgentPluginMapping> {

    /**
     * Resolved plugin rows with param JSON for runtime.
     *
     * @param agentId agent id
     * @return mappings
     */
    List<AgentPluginMapping> agentPluginParamsByAgentId(String agentId);

    /**
     * Remove all mappings for an agent.
     *
     * @param agentId agent id
     */
    void deleteByAgentId(String agentId);
}
