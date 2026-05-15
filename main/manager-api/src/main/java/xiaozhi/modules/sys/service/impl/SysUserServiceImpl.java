package xiaozhi.modules.sys.service.impl;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.toolkit.IdWorker;

import lombok.RequiredArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.jpa.JpaAuditHelper;
import xiaozhi.common.jpa.JpaPageUtils;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.security.password.PasswordUtils;
import xiaozhi.modules.sys.dto.AdminPageUserDTO;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.enums.SuperAdminEnum;
import xiaozhi.modules.sys.repository.SysUserRepository;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.service.SysUserService;
import xiaozhi.modules.sys.vo.AdminPageUserVO;

/**
 * {@link SysUserService} backed by JPA.
 */
@RequiredArgsConstructor
@Service
public class SysUserServiceImpl implements SysUserService {

    private final SysUserRepository userRepository;
    private final DeviceService deviceService;
    private final AgentService agentService;
    private final SysParamsService sysParamsService;

    @Override
    public Class<SysUserEntity> currentModelClass() {
        return SysUserEntity.class;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(SysUserEntity entity) {
        JpaAuditHelper.fillInsert(entity);
        if (entity.getId() == null) {
            entity.setId(IdWorker.getId());
        }
        userRepository.save(entity);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysUserEntity> entityList) {
        return insertBatch(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysUserEntity> entityList, int batchSize) {
        List<SysUserEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            List<SysUserEntity> batch = list.subList(i, end);
            for (SysUserEntity e : batch) {
                JpaAuditHelper.fillInsert(e);
                if (e.getId() == null) {
                    e.setId(IdWorker.getId());
                }
            }
            userRepository.saveAll(batch);
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(SysUserEntity entity) {
        if (entity.getId() == null) {
            return false;
        }
        return userRepository.findById(entity.getId()).map(existing -> {
            if (entity.getUsername() != null) {
                existing.setUsername(entity.getUsername());
            }
            if (entity.getPassword() != null) {
                existing.setPassword(entity.getPassword());
            }
            if (entity.getSuperAdmin() != null) {
                existing.setSuperAdmin(entity.getSuperAdmin());
            }
            if (entity.getStatus() != null) {
                existing.setStatus(entity.getStatus());
            }
            JpaAuditHelper.fillUpdate(existing);
            userRepository.save(existing);
            return true;
        }).orElse(false);
    }

    @Override
    public boolean update(SysUserEntity entity, Wrapper<SysUserEntity> updateWrapper) {
        throw new UnsupportedOperationException("Use domain DTO update");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysUserEntity> entityList) {
        return updateBatchById(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysUserEntity> entityList, int batchSize) {
        List<SysUserEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            for (SysUserEntity e : list.subList(i, end)) {
                updateById(e);
            }
        }
        return true;
    }

    @Override
    public SysUserEntity selectById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        return userRepository.findById(lid).orElse(null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        userRepository.deleteById(lid);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteBatchIds(Collection<? extends Serializable> idList) {
        List<Long> lids = idList.stream().map(i -> i instanceof Long ? (Long) i : Long.parseLong(i.toString())).toList();
        if (!lids.isEmpty()) {
            userRepository.deleteAllById(lids);
        }
        return true;
    }

    @Override
    public SysUserDTO getByUsername(String username) {
        return userRepository.findFirstByUsernameOrderByIdAsc(username)
                .map(e -> ConvertUtils.sourceToTarget(e, SysUserDTO.class))
                .orElse(null);
    }

    @Override
    public SysUserDTO getByUserId(Long userId) {
        return userRepository.findById(userId).map(e -> ConvertUtils.sourceToTarget(e, SysUserDTO.class)).orElse(null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void save(SysUserDTO dto) {
        SysUserEntity entity = ConvertUtils.sourceToTarget(dto, SysUserEntity.class);

        if (!isStrongPassword(entity.getPassword())) {
            throw new RenException(ErrorCode.PASSWORD_WEAK_ERROR);
        }

        String password = PasswordUtils.encode(entity.getPassword());
        entity.setPassword(password);

        long userCount = userRepository.count();
        if (userCount == 0) {
            entity.setSuperAdmin(SuperAdminEnum.YES.value());
        } else {
            entity.setSuperAdmin(SuperAdminEnum.NO.value());
        }
        entity.setStatus(1);

        insert(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteById(Long id) {
        userRepository.deleteById(id);
        deviceService.deleteByUserId(id);
        agentService.deleteAgentByUserId(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changePassword(Long userId, PasswordDTO passwordDTO) {
        SysUserEntity sysUserEntity = userRepository.findById(userId).orElse(null);

        if (null == sysUserEntity) {
            throw new RenException(ErrorCode.TOKEN_INVALID);
        }

        if (!PasswordUtils.matches(passwordDTO.getPassword(), sysUserEntity.getPassword())) {
            throw new RenException(ErrorCode.OLD_PASSWORD_ERROR);
        }

        if (!isStrongPassword(passwordDTO.getNewPassword())) {
            throw new RenException(ErrorCode.PASSWORD_WEAK_ERROR);
        }

        String password = PasswordUtils.encode(passwordDTO.getNewPassword());
        sysUserEntity.setPassword(password);

        updateById(sysUserEntity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changePasswordDirectly(Long userId, String password) {
        if (!isStrongPassword(password)) {
            throw new RenException(ErrorCode.PASSWORD_WEAK_ERROR);
        }
        SysUserEntity patch = new SysUserEntity();
        patch.setId(userId);
        patch.setPassword(PasswordUtils.encode(password));
        updateById(patch);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String resetPassword(Long userId) {
        String password = generatePassword();
        changePasswordDirectly(userId, password);
        return password;
    }

    @Override
    public PageData<AdminPageUserVO> page(AdminPageUserDTO dto) {
        Map<String, Object> params = new HashMap<>();
        params.put(Constant.PAGE, dto.getPage());
        params.put(Constant.LIMIT, dto.getLimit());
        Pageable pageable = JpaPageUtils.toPageable(params, "id", true);
        Page<SysUserEntity> page = userRepository.findAll(adminUserSpec(dto.getMobile()), pageable);
        List<AdminPageUserVO> list = page.getContent().stream().map(user -> {
            AdminPageUserVO adminPageUserVO = new AdminPageUserVO();
            adminPageUserVO.setUserid(user.getId().toString());
            adminPageUserVO.setMobile(user.getUsername());
            String deviceCount = deviceService.selectCountByUserId(user.getId()).toString();
            adminPageUserVO.setDeviceCount(deviceCount);
            adminPageUserVO.setStatus(user.getStatus());
            adminPageUserVO.setCreateDate(user.getCreateDate());
            return adminPageUserVO;
        }).toList();
        return new PageData<>(list, page.getTotalElements());
    }

    private Specification<SysUserEntity> adminUserSpec(String mobile) {
        return (root, query, cb) -> {
            if (StringUtils.isBlank(mobile)) {
                return cb.conjunction();
            }
            return cb.like(root.get("username"), "%" + mobile + "%");
        };
    }

    private boolean isStrongPassword(String password) {
        String weakPasswordRegex = "^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z]).+$";
        Pattern pattern = Pattern.compile(weakPasswordRegex);
        Matcher matcher = pattern.matcher(password);
        return matcher.matches();
    }

    private static final String CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";
    private static final Random random = new Random();

    private String generatePassword() {
        StringBuilder password = new StringBuilder();

        password.append("0123456789".charAt(random.nextInt(10)));
        password.append("abcdefghijklmnopqrstuvwxyz".charAt(random.nextInt(26)));
        password.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ".charAt(random.nextInt(26)));
        password.append("!@#$%^&*()".charAt(random.nextInt(10)));

        for (int i = 4; i < 12; i++) {
            password.append(CHARACTERS.charAt(random.nextInt(CHARACTERS.length())));
        }

        char[] passwordChars = password.toString().toCharArray();
        for (int i = 0; i < passwordChars.length; i++) {
            int randomIndex = random.nextInt(passwordChars.length);
            char temp = passwordChars[i];
            passwordChars[i] = passwordChars[randomIndex];
            passwordChars[randomIndex] = temp;
        }

        return new String(passwordChars);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changeStatus(Integer status, String[] userIds) {
        for (String userId : userIds) {
            SysUserEntity entity = new SysUserEntity();
            entity.setId(Long.parseLong(userId));
            entity.setStatus(status);
            updateById(entity);
        }
    }

    @Override
    public boolean getAllowUserRegister() {
        if (userRepository.count() == 0) {
            return true;
        }
        String v = StringUtils.trimToEmpty(
                sysParamsService.getValue(Constant.SERVER_ALLOW_USER_REGISTER, false));
        if ("false".equalsIgnoreCase(v)) {
            return false;
        }
        return true;
    }
}
