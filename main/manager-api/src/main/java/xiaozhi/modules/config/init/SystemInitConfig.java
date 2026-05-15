package xiaozhi.modules.config.init;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;

import jakarta.annotation.PostConstruct;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.sys.redis.SysParamsRedis;
import xiaozhi.modules.sys.service.SysParamsService;

@Configuration
@DependsOn("liquibase")
public class SystemInitConfig {

    @Autowired
    private SysParamsService sysParamsService;

    @Autowired
    private ConfigService configService;

    @Autowired
    private RedisUtils redisUtils;

    @Autowired
    private SysParamsRedis sysParamsRedis;

    @PostConstruct
    public void init() {
        // Bump Redis when app version changes
        String redisVersion = (String) redisUtils.get(RedisKeys.getVersionKey());
        if (!Constant.VERSION.equals(redisVersion)) {
            redisUtils.emptyAll();
            redisUtils.set(RedisKeys.getVersionKey(), Constant.VERSION);
        }

        sysParamsService.initServerSecret();
        // After DB restore, drop stale server.secret in Redis so devices re-sync from MySQL
        sysParamsRedis.delete(new String[] { Constant.SERVER_SECRET });
        configService.getConfig(false);
    }
}