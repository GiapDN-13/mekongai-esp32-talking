package xiaozhi.modules.voiceclone.dto;

import java.util.Date;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Voice clone response DTO for the client, including model name and user name.
 */
@Data
@Schema(description = "Voice clone response DTO")
public class VoiceCloneResponseDTO {

    @Schema(description = "Unique ID")
    private String id;

    @Schema(description = "Voice display name")
    private String name;

    @Schema(description = "Model ID")
    private String modelId;

    @Schema(description = "Model name")
    private String modelName;

    @Schema(description = "Voice ID")
    private String voiceId;

    @Schema(description = "Languages")
    private String languages;

    @Schema(description = "User ID (references user table)")
    private Long userId;

    @Schema(description = "User name")
    private String userName;

    @Schema(description = "Training status: 0 pending, 1 in progress, 2 success, 3 failed")
    private Integer trainStatus;

    @Schema(description = "Training error message")
    private String trainError;

    @Schema(description = "Created at")
    private Date createDate;

    @Schema(description = "Whether audio data is present")
    private Boolean hasVoice;
}
