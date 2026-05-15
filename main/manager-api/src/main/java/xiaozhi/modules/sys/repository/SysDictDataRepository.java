package xiaozhi.modules.sys.repository;

import java.util.Collection;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import xiaozhi.modules.sys.entity.SysDictDataEntity;
import xiaozhi.modules.sys.vo.SysDictDataItem;

public interface SysDictDataRepository extends JpaRepository<SysDictDataEntity, Long>, JpaSpecificationExecutor<SysDictDataEntity> {

    void deleteByDictTypeId(Long dictTypeId);

    @Query("SELECT new xiaozhi.modules.sys.vo.SysDictDataItem(d.dictLabel, d.dictValue) FROM SysDictDataEntity d, SysDictTypeEntity t WHERE d.dictTypeId = t.id AND t.dictType = :dictType ORDER BY d.sort ASC")
    List<SysDictDataItem> findDictDataItemsByDictType(@Param("dictType") String dictType);

    @Query("SELECT DISTINCT t.dictType FROM SysDictTypeEntity t WHERE t.id IN (SELECT d.dictTypeId FROM SysDictDataEntity d WHERE d.id IN :ids)")
    List<String> findDictTypesByDataIds(@Param("ids") Collection<Long> ids);

    @Query("SELECT CASE WHEN COUNT(e) > 0 THEN true ELSE false END FROM SysDictDataEntity e WHERE e.dictTypeId = :typeId AND e.dictLabel = :label AND (:excludeId IS NULL OR e.id <> :excludeId)")
    boolean existsDuplicateLabel(@Param("typeId") Long typeId, @Param("label") String label, @Param("excludeId") Long excludeId);
}
