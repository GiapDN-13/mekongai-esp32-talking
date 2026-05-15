package xiaozhi.common.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Data filtering annotation
 * Copyright (c) Xiaozhi All rights reserved.
 * Website: https://www.xiaozhi.com
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface DataFilter {
    /**
     * Table alias
     */
    String tableAlias() default "";

    /**
     * User ID
     */
    String userId() default "creator";

    /**
     * Department ID
     */
    String deptId() default "dept_id";

}