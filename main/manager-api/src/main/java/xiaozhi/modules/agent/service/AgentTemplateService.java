package xiaozhi.modules.agent.service;

import com.baomidou.mybatisplus.extension.service.IService;

import xiaozhi.modules.agent.entity.AgentTemplateEntity;

/**
 * Service for {@code ai_agent_template} rows.
 *
 * @author chenerlei
 * @createDate 2025-03-22 11:48:18
 */
public interface AgentTemplateService extends IService<AgentTemplateEntity> {

    /**
     * Default template entity used for new agents.
     *
     * @return template
     */
    AgentTemplateEntity getDefaultTemplate();

    /**
     * Patch model id on the default template after admin changes a model catalog entry.
     *
     * @param modelType logical model type key
     * @param modelId   new model id
     */
    void updateDefaultTemplateModelId(String modelType, String modelId);

    /**
     * After delete, decrement {@code sort} for templates that were ordered after the removed row.
     *
     * @param deletedSort sort value of deleted template
     */
    void reorderTemplatesAfterDelete(Integer deletedSort);

    /**
     * Next free {@code sort} (smallest gap or max+1).
     *
     * @return next sort
     */
    Integer getNextAvailableSort();
}
