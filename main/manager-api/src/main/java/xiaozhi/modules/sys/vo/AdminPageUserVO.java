package xiaozhi.modules.sys.vo;

import java.util.Date;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Admin user row for paginated listing.
 *
 * @author zjy
 * @since 2025-3-25
 */
@Data
public class AdminPageUserVO {

    @Schema(description = "Device count")
    private String deviceCount;

    @Schema(description = "Mobile number")
    private String mobile;

    @Schema(description = "Status")
    private Integer status;

    @Schema(description = "User id")
    private String userid;

    @Schema(description = "Registration time")
    private Date createDate;
}
