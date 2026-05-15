package xiaozhi.modules.security.service.impl;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.toolkit.IdWorker;

import cn.hutool.core.date.DateUtil;
import lombok.RequiredArgsConstructor;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.TokenDTO;
import xiaozhi.common.utils.HttpContextUtils;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.security.entity.SysUserTokenEntity;
import xiaozhi.modules.security.oauth2.TokenGenerator;
import xiaozhi.modules.security.repository.SysUserTokenRepository;
import xiaozhi.modules.security.service.SysUserTokenService;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.service.SysUserService;

@RequiredArgsConstructor
@Service
public class SysUserTokenServiceImpl implements SysUserTokenService {

    private final SysUserTokenRepository userTokenRepository;
    private final SysUserService sysUserService;

    /** Token TTL: 12 hours */
    private static final int EXPIRE = 3600 * 12;

    @Override
    public Class<SysUserTokenEntity> currentModelClass() {
        return SysUserTokenEntity.class;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(SysUserTokenEntity entity) {
        Date now = new Date();
        if (entity.getId() == null) {
            entity.setId(IdWorker.getId());
        }
        if (entity.getCreateDate() == null) {
            entity.setCreateDate(now);
        }
        if (entity.getUpdateDate() == null) {
            entity.setUpdateDate(now);
        }
        userTokenRepository.save(entity);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysUserTokenEntity> entityList) {
        return insertBatch(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysUserTokenEntity> entityList, int batchSize) {
        List<SysUserTokenEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            for (SysUserTokenEntity e : list.subList(i, end)) {
                insert(e);
            }
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(SysUserTokenEntity entity) {
        userTokenRepository.save(entity);
        return true;
    }

    @Override
    public boolean update(SysUserTokenEntity entity, Wrapper<SysUserTokenEntity> updateWrapper) {
        throw new UnsupportedOperationException("Use save/update on token entity");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysUserTokenEntity> entityList) {
        return updateBatchById(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysUserTokenEntity> entityList, int batchSize) {
        List<SysUserTokenEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            userTokenRepository.saveAll(list.subList(i, end));
        }
        return true;
    }

    @Override
    public SysUserTokenEntity selectById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        return userTokenRepository.findById(lid).orElse(null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        userTokenRepository.deleteById(lid);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteBatchIds(Collection<? extends Serializable> idList) {
        List<Long> lids = idList.stream().map(i -> i instanceof Long ? (Long) i : Long.parseLong(i.toString())).toList();
        if (!lids.isEmpty()) {
            userTokenRepository.deleteAllById(lids);
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<TokenDTO> createToken(Long userId) {
        String token;

        Date now = new Date();
        Date expireTime = new Date(now.getTime() + EXPIRE * 1000L);

        SysUserTokenEntity tokenEntity = userTokenRepository.findFirstByUserIdOrderByIdAsc(userId).orElse(null);
        if (tokenEntity == null) {
            token = TokenGenerator.generateValue();

            tokenEntity = new SysUserTokenEntity();
            tokenEntity.setUserId(userId);
            tokenEntity.setToken(token);
            tokenEntity.setUpdateDate(now);
            tokenEntity.setExpireDate(expireTime);

            insert(tokenEntity);
        } else {
            if (tokenEntity.getExpireDate().getTime() < System.currentTimeMillis()) {
                token = TokenGenerator.generateValue();
            } else {
                token = tokenEntity.getToken();
            }

            tokenEntity.setToken(token);
            tokenEntity.setUpdateDate(now);
            tokenEntity.setExpireDate(expireTime);

            updateById(tokenEntity);
        }

        String clientHash = HttpContextUtils.getClientCode();

        TokenDTO tokenDTO = new TokenDTO();
        tokenDTO.setToken(token);
        tokenDTO.setExpire(EXPIRE);
        tokenDTO.setClientHash(clientHash);
        return new Result<TokenDTO>().ok(tokenDTO);
    }

    @Override
    public SysUserDTO getUserByToken(String token) {
        SysUserTokenEntity userToken = userTokenRepository.findByToken(token).orElse(null);
        if (null == userToken) {
            throw new RenException(ErrorCode.TOKEN_INVALID);
        }

        Date now = new Date();
        if (userToken.getExpireDate().before(now)) {
            throw new RenException(ErrorCode.UNAUTHORIZED);
        }

        SysUserDTO userDTO = sysUserService.getByUserId(userToken.getUserId());
        if (userDTO == null) {
            throw new RenException(ErrorCode.TOKEN_INVALID);
        }
        userDTO.setPassword("");
        return userDTO;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void logout(Long userId) {
        Date expireDate = DateUtil.offsetMinute(new Date(), -1);
        userTokenRepository.logout(userId, expireDate);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changePassword(Long userId, PasswordDTO passwordDTO) {
        sysUserService.changePassword(userId, passwordDTO);

        Date expireDate = DateUtil.offsetMinute(new Date(), -1);
        userTokenRepository.logout(userId, expireDate);
    }
}
