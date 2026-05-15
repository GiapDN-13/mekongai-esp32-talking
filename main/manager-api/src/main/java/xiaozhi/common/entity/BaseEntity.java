package xiaozhi.common.entity;

import java.io.Serializable;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;

import jakarta.persistence.Column;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import lombok.Data;

/**
 * Base entity; concrete entities should extend this.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Data
@MappedSuperclass
public abstract class BaseEntity implements Serializable {
    /**
     * id
     */
    @Id
    @TableId
    @Column(nullable = false)
    private Long id;
    /**
     * Creator user id.
     */
    @TableField(fill = FieldFill.INSERT)
    @Column(name = "creator")
    private Long creator;
    /**
     * Creation time.
     */
    @TableField(fill = FieldFill.INSERT)
    @Column(name = "create_date")
    private Date createDate;
}