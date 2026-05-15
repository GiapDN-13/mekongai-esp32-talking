package xiaozhi.modules.device.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "Device row for admin device list")
public class UserShowDeviceListVO {

    @Schema(description = "App / firmware version")
    private String appVersion;

    @Schema(description = "Bound user display name")
    private String bindUserName;

    @Schema(description = "Board / hardware model")
    private String deviceType;

    @Schema(description = "Device id")
    private String id;

    @Schema(description = "MAC address")
    private String macAddress;

    @Schema(description = "OTA auto-update flag")
    private Integer otaUpgrade;

    @Schema(description = "Recent activity (short relative time)")
    private String recentChatTime;

}
