package xiaozhi.modules.security.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Request body for sending an SMS verification code.
 */
@Data
@Schema(description = "SMS verification request")
public class SmsVerificationDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Phone number")
    @NotBlank(message = "{sysuser.username.require}")
    private String phone;

    @Schema(description = "Image captcha code")
    @NotBlank(message = "{sysuser.captcha.require}")
    private String captcha;

    @Schema(description = "Captcha session id (uuid)")
    @NotBlank(message = "{sysuser.uuid.require}")
    private String captchaId;
}