package xiaozhi.modules.knowledge.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapterFactory;

/**
 * Knowledge-base module Spring configuration.
 */
@Configuration
public class KnowledgeBaseConfig {

    /**
     * Exposes {@link KnowledgeBaseAdapterFactory} as a bean.
     */
    @Bean
    public KnowledgeBaseAdapterFactory knowledgeBaseAdapterFactory() {
        return new KnowledgeBaseAdapterFactory();
    }
}
