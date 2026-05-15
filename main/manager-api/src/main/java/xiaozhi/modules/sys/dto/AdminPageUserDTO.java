package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * Query parameters for admin user pagination.
 *
 * @author zjy
 * @since 2025-3-21
 */
@Data
@Schema(description = "Admin user page query")
public class AdminPageUserDTO {

    @Schema(description = "Mobile number filter")
    private String mobile;

    @Schema(description = "Page number")
    @Min(value = 0, message = "{sort.number}")
    private String page;

    @Schema(description = "Page size")
    @Min(value = 0, message = "{sort.number}")
    private String limit;
}
