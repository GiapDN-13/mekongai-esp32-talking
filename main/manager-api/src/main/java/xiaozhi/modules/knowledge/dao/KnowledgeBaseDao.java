package xiaozhi.modules.knowledge.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;

/**
 * Mapper for knowledge base (dataset) rows.
 */
@Mapper
public interface KnowledgeBaseDao extends BaseDao<KnowledgeBaseEntity> {

    /**
     * Deletes agent–plugin mappings that reference this knowledge base id.
     *
     * @param knowledgeBaseId local knowledge base primary key
     */
    void deletePluginMappingByKnowledgeBaseId(@Param("knowledgeBaseId") String knowledgeBaseId);

    /**
     * Atomically adjusts aggregated counters on the dataset row.
     *
     * @param datasetId  RAG dataset id
     * @param docDelta   document count delta
     * @param chunkDelta chunk count delta
     * @param tokenDelta token count delta
     */
    void updateStatsAfterChange(@Param("datasetId") String datasetId,
            @Param("docDelta") Integer docDelta,
            @Param("chunkDelta") Long chunkDelta,
            @Param("tokenDelta") Long tokenDelta);

}
