package xiaozhi.common.utils;

import org.apache.commons.lang3.StringUtils;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.security.service.CaptchaService;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * SM2 decrypt + embedded captcha validation for login payloads.
 */
public class Sm2DecryptUtil {

    /**
     * Captcha prefix length inside decrypted plaintext.
     */
    private static final int CAPTCHA_LENGTH = 5;

    /**
     * Decrypt SM2 payload, validate leading captcha, return password suffix.
     *
     * @param encryptedPassword hex ciphertext from client
     * @param captchaId         captcha session id
     * @param captchaService    captcha validator
     * @param sysParamsService  SM2 key store
     * @return plaintext password (without captcha prefix)
     */
    public static String decryptAndValidateCaptcha(String encryptedPassword, String captchaId,
            CaptchaService captchaService, SysParamsService sysParamsService) {
        // Load SM2 private key
        String privateKeyStr = sysParamsService.getValue(Constant.SM2_PRIVATE_KEY, true);
        if (StringUtils.isBlank(privateKeyStr)) {
            throw new RenException(ErrorCode.SM2_KEY_NOT_CONFIGURED);
        }

        // Decrypt
        String decryptedContent;
        try {
            decryptedContent = SM2Utils.decrypt(privateKeyStr, encryptedPassword);
        } catch (Exception e) {
            throw new RenException(ErrorCode.SM2_DECRYPT_ERROR);
        }

        // First CAPTCHA_LENGTH chars = captcha, remainder = password
        if (decryptedContent.length() > CAPTCHA_LENGTH) {
            String embeddedCaptcha = decryptedContent.substring(0, CAPTCHA_LENGTH);
            String actualPassword = decryptedContent.substring(CAPTCHA_LENGTH);

            boolean embeddedCaptchaValid = captchaService.validate(captchaId, embeddedCaptcha, true);
            if (!embeddedCaptchaValid) {
                throw new RenException(ErrorCode.SMS_CAPTCHA_ERROR);
            }

            return actualPassword;
        } else if (decryptedContent.length() > 0) {
            throw new RenException(ErrorCode.SMS_CAPTCHA_ERROR);
        } else {
            throw new RenException(ErrorCode.SM2_DECRYPT_ERROR);
        }
    }
}