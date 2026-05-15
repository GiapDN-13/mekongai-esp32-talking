package xiaozhi.modules.sys.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * Dictionary data view object.
 */
@Data
@Schema(description = "Dictionary data")
public class SysDictDataVO implements Serializable {
    @Schema(description = "Primary key")
    private Long id;

    @Schema(description = "Dictionary type id")
    private Long dictTypeId;

    @Schema(description = "Label")
    private String dictLabel;

    @Schema(description = "Value")
    private String dictValue;

    @Schema(description = "Remark")
    private String remark;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Creator id")
    private Long creator;

    @Schema(description = "Creator display name")
    private String creatorName;

    @Schema(description = "Created at")
    private Date createDate;

    @Schema(description = "Last updater id")
    private Long updater;

    @Schema(description = "Last updater display name")
    private String updaterName;

    @Schema(description = "Last updated at")
    private Date updateDate;
}
