package xiaozhi.modules.security.secret;

import java.io.IOException;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.web.filter.authc.AuthenticatingFilter;
import org.springframework.web.bind.annotation.RequestMethod;

import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.utils.HttpContextUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * Filter for config API requests authenticated with the server secret.
 */
@Slf4j
@RequiredArgsConstructor
public class ServerSecretFilter extends AuthenticatingFilter {
    private final SysParamsService sysParamsService;

    @Override
    protected ServerSecretToken createToken(ServletRequest request, ServletResponse response) {
        // Obtain request token
        String token = getRequestToken((HttpServletRequest) request);

        if (StringUtils.isBlank(token)) {
            log.warn("createToken:token is empty");
            return null;
        }

        return new ServerSecretToken(token);
    }

    @Override
    protected boolean isAccessAllowed(ServletRequest request, ServletResponse response, Object mappedValue) {
        // Allow OPTIONS preflight without auth
        if (((HttpServletRequest) request).getMethod().equals(RequestMethod.OPTIONS.name())) {
            return true;
        }
        return false;
    }

    @Override
    protected boolean onAccessDenied(ServletRequest servletRequest, ServletResponse servletResponse) throws Exception {
        // Obtain and validate token
        String token = getRequestToken((HttpServletRequest) servletRequest);
        if (StringUtils.isBlank(token)) {
            // Missing token — return 401
            this.sendUnauthorizedResponse((HttpServletResponse) servletResponse, "Server secret is required");
            return false;
        }

        // Verify token matches configured secret
        String serverSecret = getServerSecret();
        if (StringUtils.isBlank(serverSecret) || !serverSecret.equals(token)) {
            // Invalid token — return 401
            this.sendUnauthorizedResponse((HttpServletResponse) servletResponse, "Invalid server secret");
            return false;
        }

        return true;
    }

    /**
     * Write a 401 JSON response body.
     */
    private void sendUnauthorizedResponse(HttpServletResponse response, String message) {
        response.setContentType("application/json;charset=utf-8");
        response.setHeader("Access-Control-Allow-Credentials", "true");
        response.setHeader("Access-Control-Allow-Origin", HttpContextUtils.getOrigin());

        try {
            String json = JsonUtils.toJsonString(new Result<Void>().error(ErrorCode.UNAUTHORIZED, message));
            response.getWriter().print(json);
        } catch (IOException e) {
            log.error("Failed to write unauthorized response", e);
        }
    }

    /**
     * Extract Bearer token from the request.
     */
    private String getRequestToken(HttpServletRequest httpRequest) {
        String token = null;
        // Read token from Authorization header
        String authorization = httpRequest.getHeader("Authorization");
        if (StringUtils.isNotBlank(authorization) && authorization.startsWith("Bearer ")) {
            token = authorization.replace("Bearer ", "");
        }
        return token;
    }

    private String getServerSecret() {
        // Read from DB to match persisted value; Redis-only could serve stale secret after DB reset
        return sysParamsService.getValue(Constant.SERVER_SECRET, false);
    }
}
