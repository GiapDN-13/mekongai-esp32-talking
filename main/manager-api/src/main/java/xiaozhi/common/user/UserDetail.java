package xiaozhi.common.user;

import java.io.Serializable;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

/**
 * Logged-in user details.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Data
public class UserDetail implements Serializable {
    private Long id;
    private String username;
    /** Always serialized so the web console can show super-admin menus (0/1). */
    @JsonProperty("superAdmin")
    @JsonInclude(JsonInclude.Include.ALWAYS)
    private Integer superAdmin;
    private String token;
    private Integer status;
}