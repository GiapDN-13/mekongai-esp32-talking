package xiaozhi.modules.security.service.impl;

import java.io.IOException;
import java.util.Random;
import java.util.concurrent.TimeUnit;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import com.wf.captcha.SpecCaptcha;
import com.wf.captcha.base.Captcha;

import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletResponse;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.security.service.CaptchaService;
import xiaozhi.modules.sms.service.SmsService;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * Image and SMS captcha service.
 */
@Service
public class CaptchaServiceImpl implements CaptchaService {
    @Resource
    private RedisUtils redisUtils;
    @Resource
    private SmsService smsService;
    @Resource
    private SysParamsService sysParamsService;
    @Value("${renren.redis.open}")
    private boolean open;
    /**
     * Local cache entries expire after 5 minutes of access.
     */
    Cache<String, String> localCache = CacheBuilder.newBuilder().maximumSize(1000)
            .expireAfterAccess(5, TimeUnit.MINUTES).build();

    @Override
    public void create(HttpServletResponse response, String uuid) throws IOException {
        response.setContentType("image/gif");
        response.setHeader("Pragma", "No-cache");
        response.setHeader("Cache-Control", "no-cache");
        response.setDateHeader("Expires", 0);

        // Generate captcha image
        SpecCaptcha captcha = new SpecCaptcha(150, 40);
        captcha.setLen(5);
        captcha.setCharType(Captcha.TYPE_DEFAULT);
        captcha.out(response.getOutputStream());

        // Store plaintext in cache
        setCache(uuid, captcha.text());
    }

    @Override
    public boolean validate(String uuid, String code, Boolean delete) {
        if (StringUtils.isBlank(code)) {
            return false;
        }
        // Load expected code from cache
        String captcha = getCache(uuid, delete);

        // Match succeeds
        if (code.equalsIgnoreCase(captcha)) {
            return true;
        }

        return false;
    }

    @Override
    public void sendSMSValidateCode(String phone) {
        // Enforce minimum interval between sends
        String lastSendTimeKey = RedisKeys.getSMSLastSendTimeKey(phone);
        // Track last send time with 60s TTL when first created
        String lastSendTime = redisUtils
                .getKeyOrCreate(lastSendTimeKey,
                        String.valueOf(System.currentTimeMillis()), 60L);
        if (lastSendTime != null) {
            long lastSendTimeLong = Long.parseLong(lastSendTime);
            long currentTime = System.currentTimeMillis();
            long timeDiff = currentTime - lastSendTimeLong;
            if (timeDiff < 60000) {
                throw new RenException(ErrorCode.SMS_SEND_TOO_FREQUENTLY, String.valueOf((60000 - timeDiff) / 1000));
            }
        }

        // Daily send count per phone
        String todayCountKey = RedisKeys.getSMSTodayCountKey(phone);
        Integer todayCount = (Integer) redisUtils.get(todayCountKey);
        if (todayCount == null) {
            todayCount = 0;
        }

        // Max sends per day from system params
        Integer maxSendCount = sysParamsService.getValueObject(
                Constant.SysMSMParam.SERVER_SMS_MAX_SEND_COUNT.getValue(),
                Integer.class);
        if (maxSendCount == null) {
            maxSendCount = 5; // default if unset
        }

        if (todayCount >= maxSendCount) {
            throw new RenException(ErrorCode.TODAY_SMS_LIMIT_REACHED);
        }

        String key = RedisKeys.getSMSValidateCodeKey(phone);
        String validateCodes = generateValidateCode(6);

        // Store SMS code
        setCache(key, validateCodes);

        // Bump daily counter
        if (todayCount == 0) {
            redisUtils.increment(todayCountKey, RedisUtils.DEFAULT_EXPIRE);
        } else {
            redisUtils.increment(todayCountKey);
        }

        // Dispatch SMS
        smsService.sendVerificationCodeSms(phone, validateCodes);
    }

    @Override
    public boolean validateSMSValidateCode(String phone, String code, Boolean delete) {
        String key = RedisKeys.getSMSValidateCodeKey(phone);
        return validate(key, code, delete);
    }

    /**
     * Random numeric code of the given length.
     *
     * @param length number of digits
     * @return generated code
     */
    private String generateValidateCode(Integer length) {
        String chars = "0123456789"; // digits only
        Random random = new Random();
        StringBuilder code = new StringBuilder();
        for (int i = 0; i < length; i++) {
            code.append(chars.charAt(random.nextInt(chars.length())));
        }
        return code.toString();
    }

    private void setCache(String key, String value) {
        if (open) {
            key = RedisKeys.getCaptchaKey(key);
            // 5 minute TTL
            redisUtils.set(key, value, 300);
        } else {
            localCache.put(key, value);
        }
    }

    private String getCache(String key, Boolean delete) {
        if (open) {
            key = RedisKeys.getCaptchaKey(key);
            String captcha = (String) redisUtils.get(key);
            // Optionally remove after read
            if (captcha != null && delete) {
                redisUtils.delete(key);
            }

            return captcha;
        }

        String captcha = localCache.getIfPresent(key);
        // Local path always evicts after read
        if (captcha != null) {
            localCache.invalidate(key);
        }
        return captcha;
    }
}