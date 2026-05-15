package xiaozhi.modules.security.service;

import xiaozhi.common.page.TokenDTO;
import xiaozhi.common.service.BaseService;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.security.entity.SysUserTokenEntity;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;

/**
 * User session token lifecycle.
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
public interface SysUserTokenService extends BaseService<SysUserTokenEntity> {

    /**
     * Issue or refresh an access token for the user.
     *
     * @param userId user id
     */
    Result<TokenDTO> createToken(Long userId);

    SysUserDTO getUserByToken(String token);

    /**
     * Invalidate sessions for the user.
     *
     * @param userId user id
     */
    void logout(Long userId);

    /**
     * Change password and revoke existing tokens.
     *
     * @param userId
     * @param passwordDTO
     */
    void changePassword(Long userId, PasswordDTO passwordDTO);

}