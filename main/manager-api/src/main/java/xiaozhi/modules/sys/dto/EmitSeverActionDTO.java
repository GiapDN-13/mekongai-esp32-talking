package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import xiaozhi.modules.sys.enums.ServerActionEnum;

/**
 * Request to trigger an action on a Python WebSocket server.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class EmitSeverActionDTO
{
    @Schema(description = "Target WebSocket URL")
    @NotEmpty(message = "Target WebSocket URL must not be empty")
    private String targetWs;

    @Schema(description = "Server action to perform")
    @NotNull(message = "Action must not be null")
    private ServerActionEnum action;
}
