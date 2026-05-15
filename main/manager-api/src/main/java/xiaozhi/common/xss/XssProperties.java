package xiaozhi.common.xss;

import java.util.Collections;
import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Data;

/**
 * {@code renren.xss.*} properties.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Data
@ConfigurationProperties(prefix = "renren.xss")
public class XssProperties {
    /**
     * Enable XSS filter when true.
     */
    private boolean enabled;
    /**
     * URL patterns excluded from filtering.
     */
    private List<String> excludeUrls = Collections.emptyList();
}
