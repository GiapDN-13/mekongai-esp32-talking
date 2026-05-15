package xiaozhi.modules.knowledge.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Enables Spring {@code @Scheduled} for knowledge-base background tasks.
 */
@Configuration
@EnableScheduling
public class RAGTaskConfig {
}
