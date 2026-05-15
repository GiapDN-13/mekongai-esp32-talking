package xiaozhi.modules.knowledge.dao;

import org.apache.ibatis.annotations.Mapper;
import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.knowledge.entity.DocumentEntity;

/**
 * Mapper for document shadow rows ({@code ai_knowledge_document}).
 */
@Mapper
public interface DocumentDao extends BaseDao<DocumentEntity> {
}
