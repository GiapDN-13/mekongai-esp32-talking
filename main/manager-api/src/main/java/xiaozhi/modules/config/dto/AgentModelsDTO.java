package xiaozhi.modules.config.dto;

import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
@Schema(description = "Request body for resolving agent model config")
public class AgentModelsDTO {

    @NotBlank(message = "Device MAC address is required")
    @Schema(description = "Device MAC address")
    private String macAddress;

    @NotBlank(message = "Client ID is required")
    @Schema(description = "Client ID")
    private String clientId;

    @NotNull(message = "Client-side instantiated models map is required")
    @Schema(description = "Models already loaded on the client (type → model id)")
    private Map<String, String> selectedModule;
}