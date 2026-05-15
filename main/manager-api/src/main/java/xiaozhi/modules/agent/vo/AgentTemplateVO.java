package xiaozhi.modules.agent.vo;

import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;

@Data
@EqualsAndHashCode(callSuper = true)
public class AgentTemplateVO extends AgentTemplateEntity {
    /** Resolved TTS / voice model display name. */
    private String ttsModelName;

    /** Resolved LLM display name. */
    private String llmModelName;
}
