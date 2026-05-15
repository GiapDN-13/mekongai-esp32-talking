package xiaozhi.modules.device.dto;

import lombok.Data;

@Data
public class DeviceManualAddDTO {
    private String agentId;
    /** Board / model string. */
    private String board;
    /** Firmware version. */
    private String appVersion;
    /** MAC address (also used as device id). */
    private String macAddress;
}
