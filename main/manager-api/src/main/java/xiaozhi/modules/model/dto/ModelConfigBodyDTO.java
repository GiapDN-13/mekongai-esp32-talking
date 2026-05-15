package xiaozhi.modules.model.dto;

import java.io.Serial;

import cn.hutool.json.JSONObject;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "Model configuration request body")
public class ModelConfigBodyDTO {

    @Serial
    private static final long serialVersionUID = 1L;

    @Schema(description = "Model id; auto-generated if omitted")
    private String id;

    @Schema(description = "Model code (e.g. AliLLM, DoubaoTTS)")
    private String modelCode;

    @Schema(description = "Display name")
    private String modelName;

    @Schema(description = "Default flag (0 no, 1 yes)")
    private Integer isDefault;

    @Schema(description = "Enabled flag")
    private Integer isEnabled;

    @Schema(description = "Config payload (JSON)")
    private JSONObject configJson;

    @Schema(description = "Official documentation URL")
    private String docLink;

    @Schema(description = "Remark")
    private String remark;

    @Schema(description = "Sort order")
    private Integer sort;
}
