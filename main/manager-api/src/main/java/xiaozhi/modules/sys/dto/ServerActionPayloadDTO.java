package xiaozhi.modules.sys.dto;

import lombok.Data;
import xiaozhi.modules.sys.enums.ServerActionEnum;

import java.util.Map;

/**
 * Payload sent to the Python server over WebSocket.
 */
@Data
public class ServerActionPayloadDTO
{
    /**
     * Payload type; console-to-server uses {@code server}.
     */
    private String type;
    /**
     * Action to run on the server.
     */
    private ServerActionEnum action;
    /**
     * Arbitrary JSON-compatible body.
     */
    private Map<String, Object> content;

    public static ServerActionPayloadDTO build(ServerActionEnum action, Map<String, Object> content) {
        ServerActionPayloadDTO serverActionPayloadDTO = new ServerActionPayloadDTO();
        serverActionPayloadDTO.setAction(action);
        serverActionPayloadDTO.setContent(content);
        serverActionPayloadDTO.setType("server");
        return serverActionPayloadDTO;
    }
    // Hidden ctor; use {@link #build}
    private ServerActionPayloadDTO() {}
}
