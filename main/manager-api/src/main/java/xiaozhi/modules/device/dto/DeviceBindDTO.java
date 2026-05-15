package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * Internal bind context (MAC + user + agent).
 *
 * @author zjy
 * @since 2025-3-28
 */
@Data
@AllArgsConstructor
@Schema(description = "Device bind context")
public class DeviceBindDTO {

    @Schema(description = "MAC address")
    private String macAddress;

    @Schema(description = "Owner user id")
    private Long userId;

    @Schema(description = "Agent id")
    private String agentId;

}
