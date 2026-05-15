package xiaozhi.modules.agent.service;

import xiaozhi.common.service.BaseService;
import xiaozhi.modules.agent.entity.AgentContextProviderEntity;

public interface AgentContextProviderService extends BaseService<AgentContextProviderEntity> {
    /**
     * Context provider row for an agent, if any.
     * @param agentId agent id
     * @return entity or null
     */
    AgentContextProviderEntity getByAgentId(String agentId);

    /**
     * Upsert providers JSON for an agent.
     * @param entity row with agentId + list
     */
    void saveOrUpdateByAgentId(AgentContextProviderEntity entity);

    /**
     * Remove context providers for an agent.
     * @param agentId agent id
     */
    void deleteByAgentId(String agentId);
}
