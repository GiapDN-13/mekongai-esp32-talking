package xiaozhi.modules.sys.service;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.AdminPageUserDTO;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.vo.AdminPageUserVO;

/**
 * System user administration.
 */
public interface SysUserService extends BaseService<SysUserEntity> {

    SysUserDTO getByUsername(String username);

    SysUserDTO getByUserId(Long userId);

    void save(SysUserDTO dto);

    /**
     * Delete a user and related devices and agents.
     *
     * @param ids user id
     */
    void deleteById(Long ids);

    /**
     * Change password after validating the current password.
     *
     * @param userId      user id
     * @param passwordDTO current and new password
     */
    void changePassword(Long userId, PasswordDTO passwordDTO);

    /**
     * Set password without checking the old value (admin flows).
     *
     * @param userId   user id
     * @param password new password
     */
    void changePasswordDirectly(Long userId, String password);

    /**
     * Reset password to a randomly generated compliant value.
     *
     * @param userId user id
     * @return generated password
     */
    String resetPassword(Long userId);

    /**
     * Paginated users for super-admin console.
     *
     * @param dto page query
     * @return page of users
     */
    PageData<AdminPageUserVO> page(AdminPageUserDTO dto);

    /**
     * Batch-update user status.
     *
     * @param status  target status
     * @param userIds user ids
     */
    void changeStatus(Integer status, String[] userIds);

    /**
     * Whether self-service registration is enabled.
     *
     * @return true if registration is allowed
     */
    boolean getAllowUserRegister();
}
