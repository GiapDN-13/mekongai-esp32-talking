package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

@Data
@Schema(description = "OTA check response (firmware, activation, transport config)")
public class DeviceReportRespDTO {
    @Schema(description = "Server time metadata")
    private ServerTime server_time;

    @Schema(description = "Device activation challenge (unbound devices)")
    private Activation activation;

    @Schema(description = "Error message when check fails")
    private String error;

    @Schema(description = "Firmware upgrade info")
    private Firmware firmware;

    @Schema(description = "WebSocket endpoint config")
    private Websocket websocket;

    @Schema(description = "MQTT gateway config")
    private MQTT mqtt;

    @Getter
    @Setter
    public static class Firmware {
        @Schema(description = "Target firmware version")
        private String version;
        @Schema(description = "Download URL (tokenized path)")
        private String url;
    }

    public static DeviceReportRespDTO createError(String message) {
        DeviceReportRespDTO resp = new DeviceReportRespDTO();
        resp.setError(message);
        return resp;
    }

    @Setter
    @Getter
    public static class Activation {
        @Schema(description = "Six-digit activation code")
        private String code;

        @Schema(description = "Human-readable hint (e.g. console URL + code)")
        private String message;

        @Schema(description = "Challenge payload (device id)")
        private String challenge;
    }

    @Getter
    @Setter
    public static class ServerTime {
        @Schema(description = "Unix timestamp (ms)")
        private Long timestamp;

        @Schema(description = "Time zone id")
        private String timeZone;

        @Schema(description = "Offset from UTC in minutes")
        private Integer timezone_offset;
    }

    @Getter
    @Setter
    public static class Websocket {
        @Schema(description = "WebSocket URL")
        private String url;
        @Schema(description = "Auth token when server.auth_enabled is true")
        private String token;
    }

    @Getter
    @Setter
    public static class MQTT {
        @Schema(description = "MQTT broker endpoint")
        private String endpoint;
        @Schema(description = "MQTT client id")
        private String client_id;
        @Schema(description = "MQTT username (often Base64 JSON)")
        private String username;
        @Schema(description = "MQTT password (HMAC signature)")
        private String password;
        @Schema(description = "Publish topic")
        private String publish_topic;
        @Schema(description = "Subscribe topic")
        private String subscribe_topic;
    }
}
