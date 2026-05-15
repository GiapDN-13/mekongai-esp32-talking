package xiaozhi.modules.device.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_device")
@Schema(description = "Device")
public class DeviceEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Device id")
    private String id;

    @Schema(description = "Owner user id")
    private Long userId;

    @Schema(description = "MAC address")
    private String macAddress;

    @Schema(description = "Last connection time")
    private Date lastConnectedAt;

    @Schema(description = "Auto OTA: 0 off, 1 on")
    private Integer autoUpdate;

    @Schema(description = "Board / hardware model")
    private String board;

    @Schema(description = "Display alias")
    private String alias;

    @Schema(description = "Agent id")
    private String agentId;

    @Schema(description = "Firmware / app version")
    private String appVersion;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Last updater user id")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Updated at")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "Creator user id")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Created at")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}