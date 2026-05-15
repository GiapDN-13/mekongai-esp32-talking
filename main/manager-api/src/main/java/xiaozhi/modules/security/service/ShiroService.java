package xiaozhi.modules.security.service;

import xiaozhi.modules.security.entity.SysUserTokenEntity;
import xiaozhi.modules.sys.entity.SysUserEntity;

/**
 * Data access backing Shiro OAuth2 realm.
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
public interface ShiroService {

    SysUserTokenEntity getByToken(String token);

    /**
     * Load user entity by id.
     *
     * @param userId
     */
    SysUserEntity getUser(Long userId);

}
