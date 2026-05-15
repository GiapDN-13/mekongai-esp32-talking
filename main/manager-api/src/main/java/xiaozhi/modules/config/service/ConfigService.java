package xiaozhi.modules.config.service;

import java.util.Map;

public interface ConfigService {
    /**
     * Build merged server configuration (optionally from Redis cache).
     *
     * @param isCache when true, return cached payload if present
     */
    Object getConfig(Boolean isCache);

    /**
     * Resolve per-device agent + model wiring for xiaozhi-server.
     *
     * @param macAddress     device MAC
     * @param selectedModule client-side models already instantiated
     */
    Map<String, Object> getAgentModels(String macAddress, Map<String, String> selectedModule);
}