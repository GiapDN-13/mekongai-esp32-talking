package xiaozhi.common.page;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Token payload for auth responses.
 *
 * @author Jack
 */
@Data
@Schema(description = "Token payload")
public class TokenDTO implements Serializable {

    @Schema(description = "Access token")
    private String token;

    @Schema(description = "Expiry time")
    private int expire;

    @Schema(description = "Client fingerprint")
    private String clientHash;
}
