package xiaozhi.modules.sys.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * Dictionary type view object.
 */
@Data
@Schema(description = "Dictionary type")
public class SysDictTypeVO implements Serializable {
    @Schema(description = "Primary key")
    private Long id;

    @Schema(description = "Type code")
    private String dictType;

    @Schema(description = "Type name")
    private String dictName;

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
