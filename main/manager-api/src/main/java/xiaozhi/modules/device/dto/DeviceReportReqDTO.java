package xiaozhi.modules.device.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;
import java.util.List;

@Setter
@Getter
@Schema(description = "Device firmware / hardware report request body")
public class DeviceReportReqDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Report payload version")
    private Integer version;

    @Schema(description = "Flash size in bytes")
    @JsonProperty("flash_size")
    private Integer flashSize;

    @Schema(description = "Minimum free heap in bytes")
    @JsonProperty("minimum_free_heap_size")
    private Integer minimumFreeHeapSize;

    @Schema(description = "Device MAC address")
    @JsonProperty("mac_address")
    private String macAddress;

    @Schema(description = "Device UUID")
    private String uuid;

    @Schema(description = "Chip model name")
    @JsonProperty("chip_model_name")
    private String chipModelName;

    @Schema(description = "Chip details")
    @JsonProperty("chip_info")
    private ChipInfo chipInfo;

    @Schema(description = "Application / firmware build info")
    private Application application;

    @Schema(description = "Partition table entries")
    @JsonProperty("partition_table")
    private List<Partition> partitionTable;

    @Schema(description = "Current running OTA partition")
    private OtaInfo ota;

    @Schema(description = "Board type and network info")
    private BoardInfo board;

    @Getter
    @Setter
    @Schema(description = "Chip info")
    public static class ChipInfo {
        @Schema(description = "Chip model code")
        private Integer model;

        @Schema(description = "CPU core count")
        private Integer cores;

        @Schema(description = "Hardware revision")
        private Integer revision;

        @Schema(description = "Feature flags bitmask")
        private Integer features;
    }

    @Getter
    @Setter
    @Schema(description = "Application build metadata")
    public static class Application {
        @Schema(description = "Application name")
        private String name;

        @Schema(description = "Application version string")
        private String version;

        @Schema(description = "Build time (UTC ISO-8601)")
        @JsonProperty("compile_time")
        private String compileTime;

        @Schema(description = "ESP-IDF version")
        @JsonProperty("idf_version")
        private String idfVersion;

        @Schema(description = "ELF SHA-256 hex digest")
        @JsonProperty("elf_sha256")
        private String elfSha256;
    }

    @Getter
    @Setter
    @Schema(description = "Flash partition entry")
    public static class Partition {
        @Schema(description = "Partition label")
        private String label;

        @Schema(description = "Partition type")
        private Integer type;

        @Schema(description = "Partition subtype")
        private Integer subtype;

        @Schema(description = "Start address")
        private Integer address;

        @Schema(description = "Partition size in bytes")
        private Integer size;
    }

    @Getter
    @Setter
    @Schema(description = "OTA slot info")
    public static class OtaInfo {
        @Schema(description = "Current OTA label")
        private String label;
    }

    @Getter
    @Setter
    @Schema(description = "Board and Wi-Fi status")
    public static class BoardInfo {
        @Schema(description = "Board type key")
        private String type;

        @Schema(description = "Connected Wi-Fi SSID")
        private String ssid;

        @Schema(description = "Wi-Fi RSSI (dBm)")
        private Integer rssi;

        @Schema(description = "Wi-Fi channel")
        private Integer channel;

        @Schema(description = "IP address")
        private String ip;

        @Schema(description = "MAC address")
        private String mac;
    }
}
