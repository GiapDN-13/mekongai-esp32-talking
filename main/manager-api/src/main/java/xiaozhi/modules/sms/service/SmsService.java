package xiaozhi.modules.sms.service;

/**
 * Contract for SMS service operations.
 *
 * @author zjy
 * @since 2025-05-12
 */
public interface SmsService {

    /**
     * Sends a verification code SMS.
     * @param phone phone number
     * @param VerificationCode verification code
     */
    void sendVerificationCodeSms(String phone, String VerificationCode) ;
}
