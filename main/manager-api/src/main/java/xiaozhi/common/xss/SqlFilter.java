package xiaozhi.common.xss;

import org.apache.commons.lang3.StringUtils;

import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;

/**
 * Naive SQL keyword guard for untrusted string parameters.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
public class SqlFilter {

    /**
     * Remove quotes/backslashes, lowercase, then reject known SQL keywords.
     *
     * @param str raw user input
     */
    public static String sqlInject(String str) {
        if (StringUtils.isBlank(str)) {
            return null;
        }
        // Strip quotes, semicolons, backslashes
        str = StringUtils.replace(str, "'", "");
        str = StringUtils.replace(str, "\"", "");
        str = StringUtils.replace(str, ";", "");
        str = StringUtils.replace(str, "\\", "");

        // Case-insensitive match
        str = str.toLowerCase();

        // Blocked keywords
        String[] keywords = { "master", "truncate", "insert", "select", "delete", "update", "declare", "alter",
                "drop" };

        // Reject if any keyword appears
        for (String keyword : keywords) {
            if (str.contains(keyword)) {
                throw new RenException(ErrorCode.INVALID_SYMBOL);
            }
        }

        return str;
    }
}
