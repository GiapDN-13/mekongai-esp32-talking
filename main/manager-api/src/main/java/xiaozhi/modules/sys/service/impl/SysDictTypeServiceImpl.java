package xiaozhi.modules.sys.service.impl;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.apache.commons.lang3.StringUtils;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.toolkit.IdWorker;

import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.jpa.JpaAuditHelper;
import xiaozhi.common.jpa.JpaPageUtils;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.sys.dto.SysDictTypeDTO;
import xiaozhi.modules.sys.entity.SysDictTypeEntity;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.repository.SysDictTypeRepository;
import xiaozhi.modules.sys.repository.SysUserRepository;
import xiaozhi.modules.sys.service.SysDictDataService;
import xiaozhi.modules.sys.service.SysDictTypeService;
import xiaozhi.modules.sys.vo.SysDictTypeVO;

/**
 * {@link xiaozhi.modules.sys.service.SysDictTypeService} backed by JPA.
 */
@Service
@RequiredArgsConstructor
public class SysDictTypeServiceImpl implements SysDictTypeService {

    private final SysDictTypeRepository dictTypeRepository;
    private final SysUserRepository sysUserRepository;
    private final SysDictDataService sysDictDataService;

    @Override
    public Class<SysDictTypeEntity> currentModelClass() {
        return SysDictTypeEntity.class;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(SysDictTypeEntity entity) {
        JpaAuditHelper.fillInsert(entity);
        if (entity.getId() == null) {
            entity.setId(IdWorker.getId());
        }
        dictTypeRepository.save(entity);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysDictTypeEntity> entityList) {
        return insertBatch(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysDictTypeEntity> entityList, int batchSize) {
        List<SysDictTypeEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            List<SysDictTypeEntity> batch = list.subList(i, end);
            for (SysDictTypeEntity e : batch) {
                JpaAuditHelper.fillInsert(e);
                if (e.getId() == null) {
                    e.setId(IdWorker.getId());
                }
            }
            dictTypeRepository.saveAll(batch);
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(SysDictTypeEntity entity) {
        JpaAuditHelper.fillUpdate(entity);
        dictTypeRepository.save(entity);
        return true;
    }

    @Override
    public boolean update(SysDictTypeEntity entity, Wrapper<SysDictTypeEntity> updateWrapper) {
        throw new UnsupportedOperationException("Use domain DTO update");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysDictTypeEntity> entityList) {
        return updateBatchById(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysDictTypeEntity> entityList, int batchSize) {
        List<SysDictTypeEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            for (SysDictTypeEntity e : list.subList(i, end)) {
                JpaAuditHelper.fillUpdate(e);
            }
            dictTypeRepository.saveAll(list.subList(i, end));
        }
        return true;
    }

    @Override
    public SysDictTypeEntity selectById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        return dictTypeRepository.findById(lid).orElse(null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        dictTypeRepository.deleteById(lid);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteBatchIds(Collection<? extends Serializable> idList) {
        List<Long> lids = idList.stream().map(id -> id instanceof Long ? (Long) id : Long.parseLong(id.toString())).toList();
        if (!lids.isEmpty()) {
            dictTypeRepository.deleteAllById(lids);
        }
        return true;
    }

    @Override
    public PageData<SysDictTypeVO> page(Map<String, Object> params) {
        Pageable pageable = JpaPageUtils.toPageable(params, "sort", true);
        Page<SysDictTypeEntity> page = dictTypeRepository.findAll(buildListSpec(params), pageable);
        PageData<SysDictTypeVO> pageData = JpaPageUtils.toPageData(page, SysDictTypeVO.class);
        setUserName(pageData.getList());
        return pageData;
    }

    private Specification<SysDictTypeEntity> buildListSpec(Map<String, Object> params) {
        String dictType = (String) params.get("dictType");
        String dictName = (String) params.get("dictName");
        return (root, query, cb) -> {
            List<Predicate> ps = new ArrayList<>();
            if (StringUtils.isNotBlank(dictType)) {
                ps.add(cb.like(root.get("dictType"), "%" + dictType + "%"));
            }
            if (StringUtils.isNotBlank(dictName)) {
                ps.add(cb.like(root.get("dictName"), "%" + dictName + "%"));
            }
            return ps.isEmpty() ? cb.conjunction() : cb.and(ps.toArray(Predicate[]::new));
        };
    }

    @Override
    public SysDictTypeVO get(Long id) {
        SysDictTypeEntity entity = dictTypeRepository.findById(id).orElse(null);
        if (entity == null) {
            throw new RenException(ErrorCode.DICT_TYPE_NOT_EXIST);
        }
        return ConvertUtils.sourceToTarget(entity, SysDictTypeVO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void save(SysDictTypeDTO dto) {
        checkDictTypeUnique(dto.getDictType(), null);
        SysDictTypeEntity entity = ConvertUtils.sourceToTarget(dto, SysDictTypeEntity.class);
        insert(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(SysDictTypeDTO dto) {
        checkDictTypeUnique(dto.getDictType(), String.valueOf(dto.getId()));
        SysDictTypeEntity entity = ConvertUtils.sourceToTarget(dto, SysDictTypeEntity.class);
        updateById(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(Long[] ids) {
        for (Long id : ids) {
            sysDictDataService.deleteByTypeId(id);
        }
        deleteBatchIds(Arrays.asList(ids));
    }

    @Override
    public List<SysDictTypeVO> list(Map<String, Object> params) {
        List<SysDictTypeEntity> entityList = dictTypeRepository.findAll(buildListSpec(params));
        List<SysDictTypeVO> voList = ConvertUtils.sourceToTarget(entityList, SysDictTypeVO.class);
        setUserName(voList);
        return voList;
    }

    private void setUserName(List<SysDictTypeVO> sysDictTypeList) {
        Set<Long> userIds = sysDictTypeList.stream().flatMap(vo -> Stream.of(vo.getCreator(), vo.getUpdater()))
                .filter(Objects::nonNull).collect(Collectors.toSet());
        if (!userIds.isEmpty()) {
            List<SysUserEntity> sysUserEntities = sysUserRepository.findAllById(userIds);
            Map<Long, String> userNameMap = sysUserEntities.stream().collect(Collectors.toMap(SysUserEntity::getId,
                    SysUserEntity::getUsername, (existing, replacement) -> existing));
            sysDictTypeList.forEach(vo -> {
                vo.setCreatorName(userNameMap.get(vo.getCreator()));
                vo.setUpdaterName(userNameMap.get(vo.getUpdater()));
            });
        }
    }

    private void checkDictTypeUnique(String dictType, String excludeId) {
        Long ex = StringUtils.isNotBlank(excludeId) ? Long.parseLong(excludeId) : null;
        if (dictTypeRepository.existsOtherWithSameDictType(dictType, ex)) {
            throw new RenException(ErrorCode.DICT_TYPE_DUPLICATE);
        }
    }
}
