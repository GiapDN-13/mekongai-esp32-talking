package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * DTO for updating an agent voice print.
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintUpdateDTO {
    /**
     * Voice-print row id.
     */
    private String id;
    /**
     * Audio file id.
     */
    private String audioId;
    /**
     * Display name of the speaker.
     */
    private String sourceName;
    /**
     * Short description of the speaker.
     */
    private String introduce;
}
