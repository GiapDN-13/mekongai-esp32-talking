package xiaozhi.modules.sys.service;

public interface TokenService {
    /**
     * Create an opaque token string for the given user.
     *
     * @param userId user id
     * @return raw token value
     */
    String createToken(long userId);
}
