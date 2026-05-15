package xiaozhi.modules.security.service.impl;

import org.springframework.stereotype.Service;

import lombok.AllArgsConstructor;
import xiaozhi.modules.security.entity.SysUserTokenEntity;
import xiaozhi.modules.security.repository.SysUserTokenRepository;
import xiaozhi.modules.security.service.ShiroService;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.repository.SysUserRepository;

@AllArgsConstructor
@Service
public class ShiroServiceImpl implements ShiroService {
    private final SysUserRepository sysUserRepository;
    private final SysUserTokenRepository sysUserTokenRepository;

    @Override
    public SysUserTokenEntity getByToken(String token) {
        return sysUserTokenRepository.findByToken(token).orElse(null);
    }

    @Override
    public SysUserEntity getUser(Long userId) {
        return sysUserRepository.findById(userId).orElse(null);
    }
}