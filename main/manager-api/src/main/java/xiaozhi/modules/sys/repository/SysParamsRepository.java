package xiaozhi.modules.sys.repository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

import xiaozhi.modules.sys.entity.SysParamsEntity;

public interface SysParamsRepository extends JpaRepository<SysParamsEntity, Long>, JpaSpecificationExecutor<SysParamsEntity> {

    Optional<SysParamsEntity> findByParamCode(String paramCode);

    @Query("select e.paramValue from SysParamsEntity e where e.paramCode = :paramCode")
    Optional<String> findParamValueByParamCode(@Param("paramCode") String paramCode);

    @Query("select e.paramCode from SysParamsEntity e where e.id in :ids")
    List<String> findParamCodesByIds(@Param("ids") Collection<Long> ids);

    @Modifying(clearAutomatically = true)
    @Transactional(rollbackFor = Exception.class)
    @Query("update SysParamsEntity e set e.paramValue = :paramValue where e.paramCode = :paramCode")
    int updateValueByParamCode(@Param("paramCode") String paramCode, @Param("paramValue") String paramValue);
}
