package xiaozhi.modules.agent.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.agent.dto.AgentCreateDTO;
import xiaozhi.modules.agent.dto.AgentDTO;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.vo.AgentInfoVO;

/**
 * Agent aggregate service.
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentService extends BaseService<AgentEntity> {
    /**
     * Paged agents for admin console.
     *
     * @param params query params
     * @return page
     */
    PageData<AgentEntity> adminAgentList(Map<String, Object> params);

    /**
     * Agent detail with plugins and context providers.
     *
     * @param id agent id
     * @return detail or null
     */
    AgentInfoVO getAgentById(String id);

    /**
     * Insert raw entity row.
     *
     * @param entity row
     * @return success
     */
    boolean insert(AgentEntity entity);

    /**
     * Delete all agents owned by a user.
     *
     * @param userId owner id
     */
    void deleteAgentByUserId(Long userId);

    /**
     * List agents for a user with optional search.
     *
     * @param userId     owner id
     * @param keyword    optional filter
     * @param searchType {@code name} or {@code mac}
     * @return list
     */
    List<AgentDTO> getUserAgents(Long userId, String keyword, String searchType);

    /**
     * Count devices bound to an agent.
     *
     * @param agentId agent id
     * @return count
     */
    Integer getDeviceCountByAgentId(String agentId);

    /**
     * Default agent for the latest device row with this MAC.
     *
     * @param macAddress device MAC
     * @return agent or null
     */
    AgentEntity getDefaultAgentByMacAddress(String macAddress);

    /**
     * Whether the user may access the agent (owner or super-admin).
     *
     * @param agentId agent id
     * @param userId  user id
     * @return allowed
     */
    boolean checkAgentPermission(String agentId, Long userId);

    /**
     * Partial update by id.
     *
     * @param agentId agent id
     * @param dto     fields to apply
     */
    void updateAgentById(String agentId, AgentUpdateDTO dto);

    /**
     * Create from minimal DTO; returns new agent id.
     *
     * @param dto create payload
     * @return new agent id
     */
    String createAgent(AgentCreateDTO dto);


}
