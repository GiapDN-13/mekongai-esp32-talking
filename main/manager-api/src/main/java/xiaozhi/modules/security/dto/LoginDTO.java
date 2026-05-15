package xiaozhi.modules.security.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Login or register payload.
 */
@Data
@Schema(description = "Login form")
public class LoginDTO implements Serializable {

    @Schema(description = "Username (often mobile number)")
    @NotBlank(message = "{sysuser.username.require}")
    private String username;

    @Schema(description = "Password (SM2-encrypted in transit when enabled)")
    @NotBlank(message = "{sysuser.password.require}")
    private String password;

    @Schema(description = "SMS verification code (register with mobile)")
    private String mobileCaptcha;

    @Schema(description = "Captcha session id (uuid)")
    @NotBlank(message = "{sysuser.uuid.require}")
    private String captchaId;

}