package xiaozhi.modules.security.user;

import org.apache.shiro.SecurityUtils;
import org.apache.shiro.subject.Subject;

import xiaozhi.common.user.UserDetail;

/**
 * Helpers for the current Shiro {@link org.apache.shiro.subject.Subject} and principal.
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
public class SecurityUser {

    public static Subject getSubject() {
        try {
            return SecurityUtils.getSubject();
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Current authenticated user detail, or empty {@link UserDetail} if none.
     */
    public static UserDetail getUser() {
        Subject subject = getSubject();
        if (subject == null) {
            return new UserDetail();
        }

        UserDetail user = (UserDetail) subject.getPrincipal();
        if (user == null) {
            return new UserDetail();
        }

        return user;
    }

    public static String getToken() {
        return getUser().getToken();
    }

    /**
     * Current user id from the security context.
     */
    public static Long getUserId() {
        return getUser().getId();
    }
}