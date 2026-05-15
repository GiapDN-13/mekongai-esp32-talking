package xiaozhi.common.utils;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.security.service.CaptchaService;
import xiaozhi.modules.sys.service.SysParamsService;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

/**
 * Unit tests for Sm2DecryptUtil — decrypt + captcha validation flow.
 */
@ExtendWith(MockitoExtension.class)
class Sm2DecryptUtilTest {

    @Mock
    private CaptchaService captchaService;

    @Mock
    private SysParamsService sysParamsService;

    @Test
    void throwsWhenPrivateKeyNotConfigured() {
        when(sysParamsService.getValue(anyString(), eq(true))).thenReturn(null);

        RenException ex = assertThrows(RenException.class, () ->
                Sm2DecryptUtil.decryptAndValidateCaptcha("encrypted", "captchaId", captchaService, sysParamsService)
        );
        assertNotNull(ex);
    }

    @Test
    void throwsWhenPrivateKeyIsBlank() {
        when(sysParamsService.getValue(anyString(), eq(true))).thenReturn("   ");

        assertThrows(RenException.class, () ->
                Sm2DecryptUtil.decryptAndValidateCaptcha("encrypted", "captchaId", captchaService, sysParamsService)
        );
    }

    @Test
    void throwsOnDecryptionFailure() {
        when(sysParamsService.getValue(anyString(), eq(true))).thenReturn("validPrivateKeyHex");

        // SM2Utils.decrypt will fail with an invalid key → RenException (SM2_DECRYPT_ERROR)
        assertThrows(RenException.class, () ->
                Sm2DecryptUtil.decryptAndValidateCaptcha("badCipherText", "captchaId", captchaService, sysParamsService)
        );
    }
}
