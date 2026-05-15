package xiaozhi.modules.knowledge.rag;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;

/**
 * Knowledge base adapter factory.
 * Creates and caches adapter instances.
 */
@Slf4j
public class KnowledgeBaseAdapterFactory {

    // type -> class
    private static final Map<String, Class<? extends KnowledgeBaseAdapter>> adapterRegistry = new HashMap<>();

    // instance cache
    private static final Map<String, KnowledgeBaseAdapter> adapterCache = new ConcurrentHashMap<>();

    // Max cached adapters
    private static final int MAX_CACHE_SIZE = 50;

    static {
        // Built-in types
        registerAdapter("ragflow", xiaozhi.modules.knowledge.rag.impl.RAGFlowAdapter.class);
        registerAdapter("qdrant", xiaozhi.modules.knowledge.rag.impl.QdrantAdapter.class);
        // Register more adapters here
    }

    /**
     * Register adapter type
     * 
     * @param adapterType  Adapter type id
     * @param adapterClass Adapter class
     */
    public static void registerAdapter(String adapterType, Class<? extends KnowledgeBaseAdapter> adapterClass) {
        if (adapterRegistry.containsKey(adapterType)) {
            log.warn("Adapter type '{}' already registered; overwriting", adapterType);
        }
        adapterRegistry.put(adapterType, adapterClass);
        log.info("Registered adapter type: {} -> {}", adapterType, adapterClass.getSimpleName());
    }

    /**
     * Get adapter instance
     * 
     * @param adapterType adapter type id
     * @param config      Config map
     * @return Adapter instance
     */
    public static KnowledgeBaseAdapter getAdapter(String adapterType, Map<String, Object> config) {
        String cacheKey = buildCacheKey(adapterType, config);

        // Cache lookup
        if (adapterCache.containsKey(cacheKey)) {
            log.debug("Adapter from cache: {}", cacheKey);
            return adapterCache.get(cacheKey);
        }

        // New adapter
        KnowledgeBaseAdapter adapter = createAdapter(adapterType, config);

        // Cache with cap
        if (adapterCache.size() >= MAX_CACHE_SIZE) {
            log.warn("Adapter cache full ({}), clearing cache (protective)", MAX_CACHE_SIZE);
            // Simple clear; consider LRU in prod
            adapterCache.clear();
        }

        adapterCache.put(cacheKey, adapter);
        log.info("Created and cached adapter: {}", cacheKey);

        return adapter;
    }

    /**
     * Get adapter without config
     * 
     * @param adapterType adapter type id
     * @return Adapter instance
     */
    public static KnowledgeBaseAdapter getAdapter(String adapterType) {
        return getAdapter(adapterType, null);
    }

    /**
     * List registered adapter types
     * 
     * @return Adapter types
     */
    public static Set<String> getRegisteredAdapterTypes() {
        return adapterRegistry.keySet();
    }

    /**
     * Whether type is registered
     * 
     * @param adapterType adapter type id
     * @return Registered
     */
    public static boolean isAdapterTypeRegistered(String adapterType) {
        return adapterRegistry.containsKey(adapterType);
    }

    /**
     * Clear adapter cache
     */
    public static void clearCache() {
        int cacheSize = adapterCache.size();
        adapterCache.clear();
        log.info("Cleared adapter cache, {} instance(s)", cacheSize);
    }

    /**
     * Evict cache entries for type
     * 
     * @param adapterType adapter type id
     */
    public static void removeCacheByType(String adapterType) {
        int removedCount = 0;
        for (String cacheKey : adapterCache.keySet()) {
            if (cacheKey.startsWith(adapterType + "@")) {
                adapterCache.remove(cacheKey);
                removedCount++;
            }
        }
        log.info("Removed adapter type '{}' cache entries, {} instance(s)", adapterType, removedCount);
    }

    /**
     * Factory status
     * 
     * @return Status map
     */
    public static Map<String, Object> getFactoryStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("registeredAdapterTypes", adapterRegistry.keySet());
        status.put("cachedAdapterCount", adapterCache.size());
        status.put("cacheKeys", adapterCache.keySet());
        return status;
    }

    /**
     * Create adapter
     * 
     * @param adapterType adapter type id
     * @param config      Config map
     * @return Adapter instance
     */
    private static KnowledgeBaseAdapter createAdapter(String adapterType, Map<String, Object> config) {
        if (!adapterRegistry.containsKey(adapterType)) {
            throw new RenException(ErrorCode.RAG_ADAPTER_TYPE_NOT_SUPPORTED,
                    "Unsupported adapter type: " + adapterType);
        }

        try {
            Class<? extends KnowledgeBaseAdapter> adapterClass = adapterRegistry.get(adapterType);
            KnowledgeBaseAdapter adapter = adapterClass.getDeclaredConstructor().newInstance();

            // init
            if (config != null) {
                adapter.initialize(config);

                // validate
                if (!adapter.validateConfig(config)) {
                    throw new RenException(ErrorCode.RAG_CONFIG_VALIDATION_FAILED,
                            "Adapter config invalid: " + adapterType);
                }
            }

            log.info("Adapter created: {}", adapterType);
            return adapter;

        } catch (Exception e) {
            log.error("createAdapter failed: {}", adapterType, e);
            throw new RenException(ErrorCode.RAG_ADAPTER_CREATION_FAILED,
                    "createAdapter failed: " + adapterType + ", error: " + e.getMessage());
        }
    }

    /**
     * Cache key
     * 
     * @param adapterType adapter type id
     * @param config      Config map
     * @return cache key
     */
    private static String buildCacheKey(String adapterType, Map<String, Object> config) {
        if (config == null || config.isEmpty()) {
            return adapterType + "@default";
        }

        // key from config
        StringBuilder keyBuilder = new StringBuilder(adapterType + "@");

        // hash in key
        int configHash = config.hashCode();
        keyBuilder.append(configHash);

        return keyBuilder.toString();
    }
}