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
 * System user (persistence).
 */
@Data
@NoArgsConstructor
@EqualsAndHashCode(callSuper = false)
@Entity
@Table(name = "sys_user")
public class SysUserEntity extends BaseEntity {
    @Column(name = "username", nullable = false, length = 50)
    private String username;

    @Column(name = "password", nullable = false, length = 255)
    private String password;

    /** Super admin: 0 no, 1 yes */
    @Column(name = "super_admin")
    private Integer superAdmin;

    /** Status: 0 disabled, 1 active */
    @Column(name = "status")
    private Integer status;

    @Column(name = "updater")
    private Long updater;

    @Column(name = "update_date")
    private Date updateDate;
}