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
@TableName("ai_ota")
@Schema(description = "OTA firmware record")
public class OtaEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Row id")
    private String id;

    @Schema(description = "Firmware display name")
    private String firmwareName;

    @Schema(description = "Firmware type / board key")
    private String type;

    @Schema(description = "Semantic version")
    private String version;

    @Schema(description = "File size in bytes")
    private Long size;

    @Schema(description = "Notes")
    private String remark;

    @Schema(description = "Stored file path")
    private String firmwarePath;

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