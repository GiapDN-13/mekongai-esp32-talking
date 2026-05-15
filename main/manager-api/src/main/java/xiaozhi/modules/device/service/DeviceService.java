package xiaozhi.modules.device.service;

import java.util.Date;
import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.device.dto.DeviceManualAddDTO;
import xiaozhi.modules.device.dto.DevicePageUserDTO;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.vo.UserShowDeviceListVO;

public interface DeviceService extends BaseService<DeviceEntity> {
    /**
     * Proxy device online status to MQTT manager API (JSON string).
     */
    String getDeviceOnlineData(String agentId);

    /**
     * OTA handshake: websocket/mqtt/firmware/activation payload for a reporting device.
     */
    DeviceReportRespDTO checkDeviceActive(String macAddress, String clientId,
            DeviceReportReqDTO deviceReport);

    /**
     * Devices bound to a user and agent.
     */
    List<DeviceEntity> getUserDevices(Long userId, String agentId);

    /**
     * Remove binding for current user.
     */
    void unbindDevice(Long userId, String deviceId);

    /**
     * Activate device with captcha from Redis.
     */
    Boolean deviceActivation(String agentId, String activationCode);

    /**
     * Delete all devices owned by a user.
     *
     * @param userId owner id
     */
    void deleteByUserId(Long userId);

    /**
     * Delete devices linked to an agent.
     *
     * @param agentId agent id
     */
    void deleteByAgentId(String agentId);

    /**
     * Count devices for a user.
     *
     * @param userId owner id
     * @return count
     */
    Long selectCountByUserId(Long userId);

    /**
     * Admin paged device list with display fields.
     *
     * @param dto page params
     * @return page
     */
    PageData<UserShowDeviceListVO> page(DevicePageUserDTO dto);

    /**
     * Lookup by MAC (exact).
     *
     * @param macAddress MAC
     * @return row or null
     */
    DeviceEntity getDeviceByMacAddress(String macAddress);

    /**
     * Activation code cached for an unbound device id.
     *
     * @param deviceId device id (MAC-shaped)
     * @return code or null
     */
    String geCodeByDeviceId(String deviceId);

    /**
     * Most recent connection time among agent devices (cached).
     *
     * @param agentId agent id
     * @return latest or null
     */
    Date getLatestLastConnectionTime(String agentId);

    /**
     * Register an already-known device row for an agent (admin-style).
     */
    void manualAddDevice(Long userId, DeviceManualAddDTO dto);

    /**
     * Update last seen (and optional app version); async when called via proxy.
     */
    void updateDeviceConnectionInfo(String agentId, String deviceId, String appVersion);

    /**
     * WebSocket auth token ({@code signature.timestamp}).
     *
     * @param clientId client id
     * @param username usually device MAC/id
     * @return token
     * @throws Exception crypto errors
     */
    String generateWebSocketToken(String clientId, String username) throws Exception;

    /**
     * Search devices by MAC substring for a user.
     *
     * @param macAddress MAC fragment
     * @param userId     owner
     * @return matches
     */
    List<DeviceEntity> searchDevicesByMacAddress(String macAddress, Long userId);

    /**
     * MCP tools list from device gateway.
     */
    Object getDeviceTools(String deviceId);

    /**
     * Invoke one MCP tool on device.
     */
    Object callDeviceTool(String deviceId, String toolName, Map<String, Object> arguments);

}
