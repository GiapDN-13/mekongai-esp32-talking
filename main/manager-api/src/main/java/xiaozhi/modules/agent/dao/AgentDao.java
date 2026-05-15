package xiaozhi.modules.agent.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import org.apache.ibatis.annotations.Select;
import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.vo.AgentInfoVO;

@Mapper
public interface AgentDao extends BaseDao<AgentEntity> {
    /**
     * Count devices bound to an agent.
     *
     * @param agentId agent id
     * @return device count
     */
    Integer getDeviceCountByAgentId(@Param("agentId") String agentId);

    /**
     * Resolve the default agent for a device by MAC (latest device row wins).
     *
     * @param macAddress device MAC
     * @return agent row or null
     */
    @Select(" SELECT a.* FROM ai_device d " +
            " LEFT JOIN ai_agent a ON d.agent_id = a.id " +
            " WHERE d.mac_address = #{macAddress} " +
            " ORDER BY d.id DESC LIMIT 1")
    AgentEntity getDefaultAgentByMacAddress(@Param("macAddress") String macAddress);

    /**
     * Load agent detail view by id (includes plugin mappings).
     *
     * @param agentId agent id
     */
    AgentInfoVO selectAgentInfoById(@Param("agentId") String agentId);
}
