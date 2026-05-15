package xiaozhi.modules.security.oauth2;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.apache.shiro.authc.IncorrectCredentialsException;
import org.apache.shiro.authc.LockedAccountException;
import org.apache.shiro.authc.DisabledAccountException;
import org.apache.shiro.authc.AuthenticationInfo;

import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.security.entity.SysUserTokenEntity;
import xiaozhi.modules.security.service.ShiroService;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.enums.SuperAdminEnum;

import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.when;

/**
 * Unit tests for Oauth2Realm — token authentication and authorization.
 */
@ExtendWith(MockitoExtension.class)
class Oauth2RealmTest {

    private Oauth2Realm realm;

    @Mock
    private ShiroService shiroService;

    @BeforeEach
    void setUp() throws Exception {
        realm = new Oauth2Realm();
        // Inject mock via reflection since @Resource is normally container-managed
        var field = Oauth2Realm.class.getDeclaredField("shiroService");
        field.setAccessible(true);
        field.set(realm, shiroService);
    }

    @Test
    void supportsOauth2Token() {
        assertTrue(realm.supports(new Oauth2Token("test-token")));
    }

    @Test
    void doesNotSupportOtherTokenTypes() {
        assertFalse(realm.supports(new org.apache.shiro.authc.UsernamePasswordToken("u", "p")));
    }

    @Test
    void throwsWhenTokenNotFound() {
        when(shiroService.getByToken(anyString())).thenReturn(null);
        Oauth2Token token = new Oauth2Token("invalid-token");
        assertThrows(IncorrectCredentialsException.class, () ->
                realm.doGetAuthenticationInfo(token)
        );
    }

    @Test
    void throwsWhenTokenExpired() {
        SysUserTokenEntity tokenEntity = new SysUserTokenEntity();
        tokenEntity.setExpireDate(new Date(System.currentTimeMillis() - 100000));
        tokenEntity.setUserId(1L);
        when(shiroService.getByToken("expired")).thenReturn(tokenEntity);

        Oauth2Token token = new Oauth2Token("expired");
        assertThrows(IncorrectCredentialsException.class, () ->
                realm.doGetAuthenticationInfo(token)
        );
    }

    @Test
    void throwsWhenAccountStatusNull() {
        SysUserTokenEntity tokenEntity = new SysUserTokenEntity();
        tokenEntity.setExpireDate(new Date(System.currentTimeMillis() + 100000));
        tokenEntity.setUserId(1L);
        when(shiroService.getByToken("valid")).thenReturn(tokenEntity);

        SysUserEntity userEntity = new SysUserEntity();
        userEntity.setId(1L);
        userEntity.setUsername("testuser");
        userEntity.setStatus(null);
        when(shiroService.getUser(1L)).thenReturn(userEntity);

        Oauth2Token token = new Oauth2Token("valid");
        assertThrows(DisabledAccountException.class, () ->
                realm.doGetAuthenticationInfo(token)
        );
    }

    @Test
    void throwsWhenAccountLocked() {
        SysUserTokenEntity tokenEntity = new SysUserTokenEntity();
        tokenEntity.setExpireDate(new Date(System.currentTimeMillis() + 100000));
        tokenEntity.setUserId(1L);
        when(shiroService.getByToken("valid")).thenReturn(tokenEntity);

        SysUserEntity userEntity = new SysUserEntity();
        userEntity.setId(1L);
        userEntity.setUsername("locked");
        userEntity.setStatus(0);
        when(shiroService.getUser(1L)).thenReturn(userEntity);

        Oauth2Token token = new Oauth2Token("valid");
        assertThrows(LockedAccountException.class, () ->
                realm.doGetAuthenticationInfo(token)
        );
    }
}
