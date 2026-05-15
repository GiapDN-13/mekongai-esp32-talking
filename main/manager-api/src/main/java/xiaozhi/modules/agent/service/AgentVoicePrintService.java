package xiaozhi.modules.agent.service;

import java.util.List;

import xiaozhi.modules.agent.dto.AgentVoicePrintSaveDTO;
import xiaozhi.modules.agent.dto.AgentVoicePrintUpdateDTO;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;

/**
 * Voice-print enrollment for agents.
 *
 * @author zjy
 */
public interface AgentVoicePrintService {
    /**
     * Register a new voice print for an agent.
     *
     * @param dto enrollment payload
     * @return success
     */
    boolean insert(AgentVoicePrintSaveDTO dto);

    /**
     * Remove a voice print (scoped to user + agent ownership checks in impl).
     *
     * @param userId       current user id
     * @param voicePrintId voice-print row id
     * @return success
     */
    boolean delete(Long userId, String voicePrintId);

    /**
     * List voice prints for an agent the user can access.
     *
     * @param userId  current user id
     * @param agentId agent id
     * @return rows
     */
    List<AgentVoicePrintVO> list(Long userId, String agentId);

    /**
     * Update metadata and optionally re-enroll audio.
     *
     * @param userId current user id
     * @param dto    update payload
     * @return success
     */
    boolean update(Long userId, AgentVoicePrintUpdateDTO dto);

}
