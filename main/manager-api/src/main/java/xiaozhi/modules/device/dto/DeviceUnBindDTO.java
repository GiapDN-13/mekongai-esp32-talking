package xiaozhi.modules.device.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Unbind request body.
 */
@Data
@Schema(description = "Device unbind request")
public class DeviceUnBindDTO implements Serializable {

    @Schema(description = "Device id")
    @NotBlank(message = "Device id is required")
    private String deviceId;

}
