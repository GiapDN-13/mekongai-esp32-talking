package xiaozhi.modules.sys.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import xiaozhi.modules.sys.entity.SysDictTypeEntity;

public interface SysDictTypeRepository extends JpaRepository<SysDictTypeEntity, Long>, JpaSpecificationExecutor<SysDictTypeEntity> {

    @Query("SELECT t.dictType FROM SysDictTypeEntity t WHERE t.id = :id")
    Optional<String> findDictTypeById(@Param("id") Long id);

    @Query("SELECT CASE WHEN COUNT(e) > 0 THEN true ELSE false END FROM SysDictTypeEntity e WHERE e.dictType = :dictType AND (:excludeId IS NULL OR e.id <> :excludeId)")
    boolean existsOtherWithSameDictType(@Param("dictType") String dictType, @Param("excludeId") Long excludeId);
}
