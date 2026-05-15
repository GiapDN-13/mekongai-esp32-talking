package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * Admin device list query.
 *
 * @author zjy
 * @since 2025-3-21
 */
@Data
@Schema(description = "Device list query")
public class DevicePageUserDTO {

    @Schema(description = "Filter by alias keyword")
    private String keywords;

    @Schema(description = "Page index")
    @Min(value = 0, message = "{page.number}")
    private String page;

    @Schema(description = "Page size")
    @Min(value = 0, message = "{limit.number}")
    private String limit;
}
