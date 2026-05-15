package xiaozhi.modules.model.dto;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * Basic LLM row for name/code pickers.
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class LlmModelBasicInfoDTO extends ModelBasicInfoDTO{
    private String type;
}
