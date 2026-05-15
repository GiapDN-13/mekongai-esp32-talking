package xiaozhi.modules.config.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.AllArgsConstructor;
import xiaozhi.common.utils.Result;
import xiaozhi.common.validator.ValidatorUtils;
import xiaozhi.modules.config.dto.AgentModelsDTO;
import xiaozhi.modules.config.service.ConfigService;

/**
 * Config endpoints for xiaozhi-server and consoles.
 *
 * @since 1.0.0
 */
@RestController
@RequestMapping("config")
@Tag(name = "Config")
@AllArgsConstructor
public class ConfigController {
    private final ConfigService configService;

    @PostMapping("server-base")
    @Operation(summary = "Get server base configuration")
    public Result<Object> getConfig() {
        Object config = configService.getConfig(true);
        return new Result<Object>().ok(config);
    }

    @PostMapping("agent-models")
    @Operation(summary = "Resolve agent model configuration for a device")
    public Result<Object> getAgentModels(@Valid @RequestBody AgentModelsDTO dto) {
        // Validate bean (javax validation)
        ValidatorUtils.validateEntity(dto);
        Object models = configService.getAgentModels(dto.getMacAddress(), dto.getSelectedModule());
        return new Result<Object>().ok(models);
    }
}
