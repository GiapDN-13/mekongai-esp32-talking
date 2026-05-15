package xiaozhi.modules.sys.controller;

import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.annotation.LogOperation;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.common.validator.AssertUtils;
import xiaozhi.common.validator.ValidatorUtils;
import xiaozhi.common.validator.group.AddGroup;
import xiaozhi.common.validator.group.DefaultGroup;
import xiaozhi.common.validator.group.UpdateGroup;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.utils.WebSocketValidator;

/**
 * System parameters management.
 *
 * @author Mark sunlightcs@gmail.com
 * @since 1.0.0
 */
@RestController
@RequestMapping("admin/params")
@Tag(name = "Parameters")
@AllArgsConstructor
public class SysParamsController {
    private final SysParamsService sysParamsService;
    private final ConfigService configService;
    private final RestTemplate restTemplate;

    @GetMapping("page")
    @Operation(summary = "Paginated list")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "Page number, starting from 1", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.LIMIT, description = "Page size", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.ORDER_FIELD, description = "Sort field", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = Constant.ORDER, description = "Sort direction: asc or desc", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = "paramCode", description = "Parameter code or remark", in = ParameterIn.QUERY, ref = "String")
    })
    @RequiresPermissions("sys:role:superAdmin")
    public Result<PageData<SysParamsDTO>> page(@Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        PageData<SysParamsDTO> page = sysParamsService.page(params);

        return new Result<PageData<SysParamsDTO>>().ok(page);
    }

    @GetMapping("{id}")
    @Operation(summary = "Get by id")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<SysParamsDTO> get(@PathVariable("id") Long id) {
        SysParamsDTO data = sysParamsService.get(id);

        return new Result<SysParamsDTO>().ok(data);
    }

    @PostMapping
    @Operation(summary = "Create")
    @LogOperation("Create parameter")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> save(@RequestBody SysParamsDTO dto) {
        // Validate payload
        ValidatorUtils.validateEntity(dto, AddGroup.class, DefaultGroup.class);

        sysParamsService.save(dto);
        configService.getConfig(false);
        return new Result<Void>();
    }

    @PutMapping
    @Operation(summary = "Update")
    @LogOperation("Update parameter")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> update(@RequestBody SysParamsDTO dto) {
        // Validate payload
        ValidatorUtils.validateEntity(dto, UpdateGroup.class, DefaultGroup.class);

        // Validate WebSocket URL list
        validateWebSocketUrls(dto.getParamCode(), dto.getParamValue());

        // Validate OTA URL
        validateOtaUrl(dto.getParamCode(), dto.getParamValue());

        // Validate MCP URL
        validateMcpUrl(dto.getParamCode(), dto.getParamValue());

        // Validate voiceprint URL
        validateVoicePrint(dto.getParamCode(), dto.getParamValue());

        // Validate MQTT secret strength
        validateMqttSecretLength(dto.getParamCode(), dto.getParamValue());

        sysParamsService.update(dto);
        configService.getConfig(false);
        return new Result<Void>();
    }

    /**
     * Validate semicolon-separated WebSocket URLs.
     *
     * @param urls Semicolon-separated WebSocket URLs
     */
    private void validateWebSocketUrls(String paramCode, String urls) {
        if (!paramCode.equals(Constant.SERVER_WEBSOCKET)) {
            return;
        }
        String[] wsUrls = urls.split("\\;");
        if (wsUrls.length == 0) {
            throw new RenException(ErrorCode.WEBSOCKET_URLS_EMPTY);
        }
        for (String url : wsUrls) {
            if (StringUtils.isNotBlank(url)) {
                // Reject localhost / loopback
                if (url.contains("localhost") || url.contains("127.0.0.1")) {
                    throw new RenException(ErrorCode.WEBSOCKET_URL_LOCALHOST);
                }

                // Validate WebSocket URL format
                if (!WebSocketValidator.validateUrlFormat(url)) {
                    throw new RenException(ErrorCode.WEBSOCKET_URL_FORMAT_ERROR);
                }

                // Test WebSocket connectivity
                if (!WebSocketValidator.testConnection(url)) {
                    throw new RenException(ErrorCode.WEBSOCKET_CONNECTION_FAILED);
                }
            }
        }
    }

    @PostMapping("/delete")
    @Operation(summary = "Delete")
    @LogOperation("Delete parameters")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> delete(@RequestBody String[] ids) {
        // Validate ids
        AssertUtils.isArrayEmpty(ids, "id");

        sysParamsService.delete(ids);
        configService.getConfig(false);
        return new Result<Void>();
    }

    /**
     * Validate OTA base URL.
     */
    private void validateOtaUrl(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_OTA)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            return;
        }

        // Reject localhost / loopback
        if (url.contains("localhost") || url.contains("127.0.0.1")) {
            throw new RenException(ErrorCode.OTA_URL_LOCALHOST);
        }

        // Validate URL shape
        if (!url.toLowerCase().startsWith("http")) {
            throw new RenException(ErrorCode.OTA_URL_PROTOCOL_ERROR);
        }
        if (!url.endsWith("/ota/")) {
            throw new RenException(ErrorCode.OTA_URL_FORMAT_ERROR);
        }

        try {
            // GET probe
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException(ErrorCode.OTA_INTERFACE_ACCESS_FAILED);
            }
            // Response should mention OTA
            String body = response.getBody();
            if (body == null || !body.contains("OTA")) {
                throw new RenException(ErrorCode.OTA_INTERFACE_FORMAT_ERROR);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.OTA_INTERFACE_VALIDATION_FAILED);
        }
    }

    private void validateMcpUrl(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_MCP_ENDPOINT)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            return;
        }
        if (url.contains("localhost") || url.contains("127.0.0.1")) {
            throw new RenException(ErrorCode.MCP_URL_LOCALHOST);
        }
        if (!url.toLowerCase().contains("key")) {
            throw new RenException(ErrorCode.MCP_URL_INVALID);
        }

        try {
            // GET probe
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException(ErrorCode.MCP_INTERFACE_ACCESS_FAILED);
            }
            // Response should indicate success
            String body = response.getBody();
            if (body == null || !body.contains("success")) {
                throw new RenException(ErrorCode.MCP_INTERFACE_FORMAT_ERROR);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.MCP_INTERFACE_VALIDATION_FAILED);
        }
    }

    // Validate voiceprint HTTP endpoint
    private void validateVoicePrint(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_VOICE_PRINT)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            return;
        }
        if (url.contains("localhost") || url.contains("127.0.0.1")) {
            throw new RenException(ErrorCode.VOICEPRINT_URL_LOCALHOST);
        }
        if (!url.toLowerCase().contains("key")) {
            throw new RenException(ErrorCode.VOICEPRINT_URL_INVALID);
        }
        // Require HTTP(S)
        if (!url.toLowerCase().startsWith("http")) {
            throw new RenException(ErrorCode.VOICEPRINT_URL_PROTOCOL_ERROR);
        }
        try {
            // GET probe
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException(ErrorCode.VOICEPRINT_INTERFACE_ACCESS_FAILED);
            }
            // Expect health marker in body
            String body = response.getBody();
            if (body == null || !body.contains("healthy")) {
                throw new RenException(ErrorCode.VOICEPRINT_INTERFACE_FORMAT_ERROR);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.VOICEPRINT_INTERFACE_VALIDATION_FAILED);
        }
    }

    // Validate MQTT secret length and complexity
    private void validateMqttSecretLength(String paramCode, String secret) {
        if (!paramCode.equals(Constant.SERVER_MQTT_SECRET)) {
            return;
        }
        if (StringUtils.isBlank(secret) || secret.equals("null")) {
            throw new RenException(ErrorCode.MQTT_SECRET_EMPTY);
        }
        if (secret.length() < 8) {
            throw new RenException(ErrorCode.MQTT_SECRET_LENGTH_INSECURE);
        }
        // Require both upper and lower case
        if (!secret.matches(".*[a-z].*") || !secret.matches(".*[A-Z].*")) {
            throw new RenException(ErrorCode.MQTT_SECRET_CHARACTER_INSECURE);
        }
        // Reject common weak substrings
        String[] weakPasswords = { "test", "1234", "admin", "password", "qwerty", "xiaozhi" };
        for (String weakPassword : weakPasswords) {
            if (secret.toLowerCase().contains(weakPassword)) {
                throw new RenException(ErrorCode.MQTT_SECRET_WEAK_PASSWORD);
            }
        }
    }
}
