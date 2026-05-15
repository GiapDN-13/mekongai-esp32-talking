package xiaozhi.modules.security.service;

import java.io.IOException;

import jakarta.servlet.http.HttpServletResponse;

/**
 * Image and SMS verification codes.
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
public interface CaptchaService {

    /**
     * Render a graphical captcha into the HTTP response.
     */
    void create(HttpServletResponse response, String uuid) throws IOException;

    /**
     * Verify a captcha code against cached value.
     *
     * @param uuid   cache key fragment
     * @param code   user-supplied code
     * @param delete whether to remove the entry after successful read
     * @return true if valid, false otherwise
     */
    boolean validate(String uuid, String code, Boolean delete);

    /**
     * Send an SMS verification code to the phone number.
     *
     * @param phone E.164 or local mobile as configured
     */
    void sendSMSValidateCode(String phone);

    /**
     * Verify SMS code for the phone number.
     *
     * @param phone  phone number
     * @param code   user-supplied code
     * @param delete whether to remove after validation
     * @return true if valid, false otherwise
     */
    boolean validateSMSValidateCode(String phone, String code, Boolean delete);
}
