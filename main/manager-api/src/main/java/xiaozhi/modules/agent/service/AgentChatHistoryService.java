package xiaozhi.modules.agent.service;

import java.util.List;
import java.util.Map;

import com.baomidou.mybatisplus.extension.service.IService;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.agent.dto.AgentChatHistoryDTO;
import xiaozhi.modules.agent.dto.AgentChatSessionDTO;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.vo.AgentChatHistoryUserVO;

/**
 * Chat history persistence and queries.
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentChatHistoryService extends IService<AgentChatHistoryEntity> {

    /**
     * Paged sessions for an agent.
     *
     * @param params includes agentId, page, limit
     * @return page
     */
    PageData<AgentChatSessionDTO> getSessionListByAgentId(Map<String, Object> params);

    /**
     * All messages in one session.
     *
     * @param agentId   agent id
     * @param sessionId session id
     * @return messages
     */
    List<AgentChatHistoryDTO> getChatHistoryBySessionId(String agentId, String sessionId);

    /**
     * Delete history for an agent; optionally drop linked audio / text.
     *
     * @param agentId     agent id
     * @param deleteAudio delete audio blobs
     * @param deleteText  delete text rows
     */
    void deleteByAgentId(String agentId, Boolean deleteAudio, Boolean deleteText);

    /**
     * Recent user messages for UI (up to ~50), including audio ids.
     *
     * @param agentId agent id
     * @return rows
     */
    List<AgentChatHistoryUserVO> getRecentlyFiftyByAgentId(String agentId);

    /**
     * Message text by audio reference id.
     *
     * @param audioId audio id
     * @return content or null
     */
    String getContentByAudioId(String audioId);


    /**
     * Whether exactly one history row ties this audio to the agent.
     *
     * @param audioId audio id
     * @param agentId agent id
     * @return true if owned
     */
    boolean isAudioOwnedByAgent(String audioId,String agentId);
}
