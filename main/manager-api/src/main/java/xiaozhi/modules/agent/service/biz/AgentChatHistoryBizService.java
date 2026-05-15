package xiaozhi.modules.agent.service.biz;

import xiaozhi.modules.agent.dto.AgentChatHistoryReportDTO;

/**
 * Chat history ingest from devices.
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentChatHistoryBizService {

    /**
     * Persist a device-reported chat row (and optional audio).
     *
     * @param agentChatHistoryReportDTO payload (MAC, session, content, optional Base64 audio, etc.)
     * @return {@code true} if accepted
     */
    Boolean report(AgentChatHistoryReportDTO agentChatHistoryReportDTO);
}
