package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.io.Serializable;

/**
 * Password recovery request payload.
 */
@Data
@Schema(description = "Password recovery")
public class RetrievePasswordDTO implements Serializable {

    @Schema(description = "Mobile number")
    @NotBlank(message = "{sysuser.password.require}")
    private String phone;

    @Schema(description = "SMS or one-time code")
    @NotBlank(message = "{sysuser.password.require}")
    private String code;

    @Schema(description = "New password")
    @NotBlank(message = "{sysuser.password.require}")
    private String password;

    @Schema(description = "Captcha id")
    @NotBlank(message = "{sysuser.uuid.require}")
    private String captchaId;



}