package xiaozhi.modules.security.config;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

import org.apache.shiro.mgt.SecurityManager;
import org.apache.shiro.session.mgt.SessionManager;
import org.apache.shiro.spring.LifecycleBeanPostProcessor;
import org.apache.shiro.spring.security.interceptor.AuthorizationAttributeSourceAdvisor;
import org.apache.shiro.spring.web.ShiroFilterFactoryBean;
import org.apache.shiro.web.config.ShiroFilterConfiguration;
import org.apache.shiro.web.mgt.DefaultWebSecurityManager;
import org.apache.shiro.web.session.mgt.DefaultWebSessionManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import jakarta.servlet.Filter;
import xiaozhi.modules.security.oauth2.Oauth2Filter;
import xiaozhi.modules.security.oauth2.Oauth2Realm;
import xiaozhi.modules.security.secret.ServerSecretFilter;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * Apache Shiro configuration.
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
@Configuration
public class ShiroConfig {

    @Bean
    public DefaultWebSessionManager sessionManager() {
        DefaultWebSessionManager sessionManager = new DefaultWebSessionManager();
        sessionManager.setSessionValidationSchedulerEnabled(false);
        sessionManager.setSessionIdUrlRewritingEnabled(false);

        return sessionManager;
    }

    @Bean("securityManager")
    public SecurityManager securityManager(Oauth2Realm oAuth2Realm, SessionManager sessionManager) {
        DefaultWebSecurityManager securityManager = new DefaultWebSecurityManager();
        securityManager.setRealm(oAuth2Realm);
        securityManager.setSessionManager(sessionManager);
        securityManager.setRememberMeManager(null);
        return securityManager;
    }

    @Bean("shiroFilter")
    public ShiroFilterFactoryBean shirFilter(SecurityManager securityManager, SysParamsService sysParamsService) {
        ShiroFilterConfiguration config = new ShiroFilterConfiguration();
        config.setFilterOncePerRequest(true);

        ShiroFilterFactoryBean shiroFilter = new ShiroFilterFactoryBean();
        shiroFilter.setSecurityManager(securityManager);
        shiroFilter.setShiroFilterConfiguration(config);

        Map<String, Filter> filters = new HashMap<>();
        // OAuth2 bearer filter
        filters.put("oauth2", new Oauth2Filter());
        // Server secret filter for internal/config APIs
        filters.put("server", new ServerSecretFilter(sysParamsService));
        shiroFilter.setFilters(filters);

        // Shiro built-in filter names (chain values below)
        /*
         * anon: no authentication required
         * authc: must be authenticated
         * user: requires "remember me" when used
         * perms: requires permission on a resource
         * role: requires a role
         */
        Map<String, String> filterMap = new LinkedHashMap<>();
        filterMap.put("/ota/**", "anon");
        filterMap.put("/otaMag/download/**", "anon");
        filterMap.put("/webjars/**", "anon");
        filterMap.put("/v3/api-docs/**", "anon");
        filterMap.put("/doc.html", "anon");
        filterMap.put("/favicon.ico", "anon");
        filterMap.put("/user/captcha", "anon");
        filterMap.put("/user/smsVerification", "anon");
        filterMap.put("/user/login", "anon");
        filterMap.put("/user/pub-config", "anon");
        filterMap.put("/user/register", "anon");
        filterMap.put("/user/retrieve-password", "anon");
        // Protect /config and selected agent routes with server secret
        filterMap.put("/config/**", "server");
        filterMap.put("/agent/chat-history/report", "server");
        filterMap.put("/agent/chat-history/download/**", "anon");
        filterMap.put("/agent/chat-summary/**", "server");
        filterMap.put("/agent/play/**", "anon");
        filterMap.put("/voiceClone/play/**", "anon");
        filterMap.put("/**", "oauth2");
        shiroFilter.setFilterChainDefinitionMap(filterMap);

        return shiroFilter;
    }

    @Bean("lifecycleBeanPostProcessor")
    public LifecycleBeanPostProcessor lifecycleBeanPostProcessor() {
        return new LifecycleBeanPostProcessor();
    }

    @Bean
    public AuthorizationAttributeSourceAdvisor authorizationAttributeSourceAdvisor(SecurityManager securityManager) {
        AuthorizationAttributeSourceAdvisor advisor = new AuthorizationAttributeSourceAdvisor();
        advisor.setSecurityManager(securityManager);
        return advisor;
    }
}
