package xiaozhi.modules.security.oauth2;

import org.apache.shiro.authc.AuthenticationToken;

/**
 * Bearer token wrapper for Shiro authentication.
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
public class Oauth2Token implements AuthenticationToken {
    private String token;

    public Oauth2Token(String token) {
        this.token = token;
    }

    @Override
    public String getPrincipal() {
        return token;
    }

    @Override
    public Object getCredentials() {
        return token;
    }
}
