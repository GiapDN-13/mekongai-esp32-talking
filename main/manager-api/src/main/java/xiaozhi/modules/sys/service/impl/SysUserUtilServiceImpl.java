package xiaozhi.modules.sys.service.impl;

import java.util.function.Consumer;

import org.springframework.stereotype.Service;

import lombok.AllArgsConstructor;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.repository.SysUserRepository;
import xiaozhi.modules.sys.service.SysUserUtilService;

@Service
@AllArgsConstructor
public class SysUserUtilServiceImpl implements SysUserUtilService {

    private final SysUserRepository userRepository;
    private final RedisUtils redisUtils;

    @Override
    public void assignUsername(Long userId, Consumer<String> setter) {
        String userIdKey = RedisKeys.getUserIdKey(userId);

        Object value = redisUtils.get(userIdKey);
        String username = (value != null) ? value.toString() : null;
        if (username != null) {
            setter.accept(username);
        } else {
            SysUserEntity entity = userRepository.findById(userId).orElse(null);
            if (entity != null) {
                username = entity.getUsername();
                redisUtils.set(userIdKey, username, 10);
                setter.accept(username);
            }
        }
    }
}
