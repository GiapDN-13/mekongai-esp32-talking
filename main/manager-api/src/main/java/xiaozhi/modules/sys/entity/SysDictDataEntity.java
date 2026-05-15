package xiaozhi.modules.sys.entity;

import java.util.Date;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import xiaozhi.common.entity.BaseEntity;

/**
 * Dictionary data row (persistence).
 */
@Data
@NoArgsConstructor
@EqualsAndHashCode(callSuper = false)
@Entity
@Table(name = "sys_dict_data")
public class SysDictDataEntity extends BaseEntity {
    @Column(name = "dict_type_id")
    private Long dictTypeId;

    @Column(name = "dict_label", length = 255)
    private String dictLabel;

    @Column(name = "dict_value", length = 255)
    private String dictValue;

    @Column(name = "remark", length = 255)
    private String remark;

    @Column(name = "sort")
    private Integer sort;

    @Column(name = "updater")
    private Long updater;

    @Column(name = "update_date")
    private Date updateDate;
}