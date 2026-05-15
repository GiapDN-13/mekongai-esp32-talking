package xiaozhi.modules.sys.service;


import java.util.function.Consumer;

/**
 * Small helper to resolve usernames without creating circular dependencies between modules
 * (e.g. user vs device).
 *
 * @author zjy
 * @since 2025-4-2
 */
public interface SysUserUtilService {
    /**
     * Load username for {@code userId} and pass it to {@code setter}.
     *
     * @param userId user id
     * @param setter consumer receiving the username
     */
    void assignUsername( Long userId, Consumer<String> setter);
}
