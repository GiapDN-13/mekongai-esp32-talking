package xiaozhi.modules.agent.dao;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.agent.entity.AgentTemplateEntity;

/**
 * Mapper for {@code ai_agent_template} (agent configuration templates).
 *
 * @author chenerlei
 * @createDate 2025-03-22 11:48:18
 */
@Mapper
public interface AgentTemplateDao extends BaseMapper<AgentTemplateEntity> {

}
