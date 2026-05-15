package xiaozhi.modules.agent.dao;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;

/**
 * DAO for {@link AgentChatHistoryEntity} (agent chat history).
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
@Mapper
public interface AiAgentChatHistoryDao extends BaseMapper<AgentChatHistoryEntity> {

    /**
     * Delete chat history rows for an agent.
     *
     * @param agentId agent id
     */
    void deleteHistoryByAgentId(String agentId);

    /**
     * Clear audio id references for an agent.
     *
     * @param agentId agent id
     */
    void deleteAudioIdByAgentId(String agentId);

    /**
     * List all audio ids referenced by an agent's chat history.
     *
     * @param agentId agent id
     * @return audio ids
     */
    List<String> getAudioIdsByAgentId(String agentId);

    /**
     * Delete audio blobs by ids.
     *
     * @param audioIds audio ids
     */
    void deleteAudioByIds(@Param("audioIds") List<String> audioIds);
}
