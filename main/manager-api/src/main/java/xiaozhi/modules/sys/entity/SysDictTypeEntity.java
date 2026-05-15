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
 * Dictionary type (persistence).
 */
@Data
@NoArgsConstructor
@EqualsAndHashCode(callSuper = false)
@Entity
@Table(name = "sys_dict_type")
public class SysDictTypeEntity extends BaseEntity {
    @Column(name = "dict_type", length = 100)
    private String dictType;

    @Column(name = "dict_name", length = 255)
    private String dictName;

    @Column(name = "remark", length = 255)
    private String remark;

    @Column(name = "sort")
    private Integer sort;

    @Column(name = "updater")
    private Long updater;

    @Column(name = "update_date")
    private Date updateDate;
}