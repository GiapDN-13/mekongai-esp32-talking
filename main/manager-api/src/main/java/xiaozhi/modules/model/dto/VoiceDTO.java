package xiaozhi.modules.model.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "TTS voice")
public class VoiceDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Voice id")
    private String id;

    @Schema(description = "Voice name")
    private String name;

    @Schema(description = "Demo audio URL")
    private String voiceDemo;
    
    @Schema(description = "Language tag(s)")
    private String languages;
    
    @Schema(description = "Whether this is a cloned voice")
    private Boolean isClone;

    public VoiceDTO(String id, String name) {
        this.id = id;
        this.name = name;
        this.voiceDemo = null;
        this.languages = null;
        this.isClone = false;
    }
    
    public VoiceDTO(String id, String name, String voiceDemo) {
        this.id = id;
        this.name = name;
        this.voiceDemo = voiceDemo;
        this.languages = null;
        this.isClone = false;
    }

}
