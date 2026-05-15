package xiaozhi.common.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;

/**
 * Redis aspect processing class
 * Copyright (c) Xiaozhi All rights reserved.
 * Website: https://www.xiaozhi.com
 */
@Slf4j
@Aspect
@Component
public class RedisAspect {
    /**
     * Enable Redis cache when true; disable when false.
     */
    @Value("${renren.redis.open}")
    private boolean open;

    @Around("execution(* xiaozhi.common.redis.RedisUtils.*(..))")
    public Object around(ProceedingJoinPoint point) throws Throwable {
        Object result = null;
        if (open) {
            try {
                result = point.proceed();
            } catch (Exception e) {
                log.error("redis error", e);
                throw new RenException(ErrorCode.REDIS_ERROR);
            }
        }
        return result;
    }
}
