package xiaozhi.modules.security.entity;

import java.io.Serializable;
import java.util.Date;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Persisted access token for a system user.
 */
@Data
@NoArgsConstructor
@Entity
@Table(name = "sys_user_token")
public class SysUserTokenEntity implements Serializable {

    @Id
    @Column(nullable = false)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "token", nullable = false, length = 255)
    private String token;

    @Column(name = "expire_date")
    private Date expireDate;

    @Column(name = "update_date")
    private Date updateDate;

    @Column(name = "create_date")
    private Date createDate;
}
