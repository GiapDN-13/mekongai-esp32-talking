package xiaozhi.common.config;

import org.springframework.context.MessageSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.context.support.ResourceBundleMessageSource;

/**
 * Ensures a real {@link ResourceBundleMessageSource} is registered as {@code messageSource}.
 * Relying only on the context default can leave an empty {@code DelegatingMessageSource} in some
 * startup orders, which breaks {@link xiaozhi.common.utils.MessageUtils}.
 */
@Configuration
public class I18nMessageSourceConfig {

    @Bean(name = "messageSource")
    @Primary
    public MessageSource messageSource() {
        ResourceBundleMessageSource source = new ResourceBundleMessageSource();
        source.setBasenames("i18n/messages");
        source.setDefaultEncoding("UTF-8");
        source.setFallbackToSystemLocale(true);
        return source;
    }
}
