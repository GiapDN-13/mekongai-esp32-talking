package xiaozhi.modules.sys.entity;

import java.util.Date;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * System parameter (persistence).
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Entity
@Table(name = "sys_params")
@Schema(description = "System parameter")
public class SysParamsEntity extends BaseEntity {
    @Column(name = "param_code", length = 32)
    @Schema(description = "Parameter code")
    private String paramCode;

    @Column(name = "param_value", length = 2000)
    @Schema(description = "Parameter value")
    private String paramValue;

    @Column(name = "value_type", length = 20)
    @Schema(description = "Value type")
    private String valueType;

    @Column(name = "param_type")
    @Schema(description = "Type: 0 system, 1 non-system")
    private Integer paramType;

    @Column(name = "remark", length = 200)
    @Schema(description = "Remark")
    private String remark;

    @Column(name = "updater")
    @Schema(description = "Last updater id")
    private Long updater;

    @Column(name = "update_date")
    @Schema(description = "Last update time")
    private Date updateDate;
}
