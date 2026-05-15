package xiaozhi.modules.sys.dto;

import lombok.Data;
import xiaozhi.modules.sys.enums.ServerActionResponseEnum;

import java.util.Map;

/**
 * Response envelope from the Python server for console actions.
 */
@Data
public class ServerActionResponseDTO
{
    private ServerActionResponseEnum status;
    private String message;
    private String type;
    /** May be replaced by typed subclasses per use case. */
    private Map<String, Object> content;
    public static final String DEFAULT_TYPE_FORM_SERVER = "server";

    public static Boolean isSuccess(ServerActionResponseDTO actionResponseDTO) {
        System.out.println(actionResponseDTO);
        if (actionResponseDTO == null) {
            return false;
        }
        if (actionResponseDTO.getStatus() == null || !actionResponseDTO.getStatus().equals(ServerActionResponseEnum.SUCCESS)) {
            return false;
        }
        Object actionType = actionResponseDTO.getContent().get("action");
        if (actionType == null) {
            return false;
        }
        return actionResponseDTO.getType() != null && actionResponseDTO.getType().equals(DEFAULT_TYPE_FORM_SERVER);
    }
}
