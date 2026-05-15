package xiaozhi.modules.agent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

/**
 * Voice-print identification API response.
 */
@Data
public class IdentifyVoicePrintResponse {
    /**
     * Best-matching voice-print id.
     */
    @JsonProperty("speaker_id")
    private String speakerId;
    /**
     * Match score.
     */
    private Double score;
}
