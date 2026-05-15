package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * DTO for creating an agent voice print.
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintSaveDTO {
    /**
     * Agent id.
     */
    private String agentId;
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
    /**
     * When true the voiceprint was already registered directly with the
     * voiceprint micro-service (e.g. via browser recording / file upload).
     * The backend should skip audio lookup and voiceprint-service registration.
     */
    private Boolean directRegistered;
    /**
     * Speaker id used during direct registration (only relevant when
     * {@link #directRegistered} is {@code true}).
     */
    private String speakerId;
}
