package xiaozhi.common.utils;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ResourceLoader;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.exception.ErrorCode;


import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

/**
 * Classpath resource loader.
 */
@AllArgsConstructor
@Slf4j
@Component
public class ResourcesUtils {
    private ResourceLoader resourceLoader;

    /**
     * Read a classpath resource as UTF-8 text.
     *
     * @param fileName path under {@code src/main/resources} (e.g. {@code lua/foo.lua})
     */
    public String loadString(String fileName)  {
        Resource resource = resourceLoader.getResource("classpath:" + fileName);
        StringBuilder luaScriptBuilder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(resource.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                luaScriptBuilder.append(line).append("\n");
            }
        }  catch (IOException e){
            log.error("loadString() failed for {}: {}", fileName, e.getMessage());
            throw new RenException(ErrorCode.RESOURCE_READ_ERROR);
        }
        return luaScriptBuilder.toString();
    }
}
