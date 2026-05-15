package xiaozhi.modules.sys.service.impl;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
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
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.ToolUtil;
import xiaozhi.modules.sys.dto.SysDictDataDTO;
import xiaozhi.modules.sys.entity.SysDictDataEntity;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.repository.SysDictDataRepository;
import xiaozhi.modules.sys.repository.SysDictTypeRepository;
import xiaozhi.modules.sys.repository.SysUserRepository;
import xiaozhi.modules.sys.service.SysDictDataService;
import xiaozhi.modules.sys.vo.SysDictDataItem;
import xiaozhi.modules.sys.vo.SysDictDataVO;

/**
 * {@link xiaozhi.modules.sys.service.SysDictDataService} backed by JPA.
 */
@Service
@RequiredArgsConstructor
public class SysDictDataServiceImpl implements SysDictDataService {

    private final SysDictDataRepository dictDataRepository;
    private final SysDictTypeRepository dictTypeRepository;
    private final SysUserRepository sysUserRepository;
    private final RedisUtils redisUtils;

    @Override
    public Class<SysDictDataEntity> currentModelClass() {
        return SysDictDataEntity.class;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(SysDictDataEntity entity) {
        JpaAuditHelper.fillInsert(entity);
        if (entity.getId() == null) {
            entity.setId(IdWorker.getId());
        }
        dictDataRepository.save(entity);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysDictDataEntity> entityList) {
        return insertBatch(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysDictDataEntity> entityList, int batchSize) {
        List<SysDictDataEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            List<SysDictDataEntity> batch = list.subList(i, end);
            for (SysDictDataEntity e : batch) {
                JpaAuditHelper.fillInsert(e);
                if (e.getId() == null) {
                    e.setId(IdWorker.getId());
                }
            }
            dictDataRepository.saveAll(batch);
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(SysDictDataEntity entity) {
        JpaAuditHelper.fillUpdate(entity);
        dictDataRepository.save(entity);
        return true;
    }

    @Override
    public boolean update(SysDictDataEntity entity, Wrapper<SysDictDataEntity> updateWrapper) {
        throw new UnsupportedOperationException("Use domain DTO update");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysDictDataEntity> entityList) {
        return updateBatchById(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysDictDataEntity> entityList, int batchSize) {
        List<SysDictDataEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            for (SysDictDataEntity e : list.subList(i, end)) {
                JpaAuditHelper.fillUpdate(e);
            }
            dictDataRepository.saveAll(list.subList(i, end));
        }
        return true;
    }

    @Override
    public SysDictDataEntity selectById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        return dictDataRepository.findById(lid).orElse(null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        dictDataRepository.deleteById(lid);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteBatchIds(Collection<? extends Serializable> idList) {
        List<Long> lids = idList.stream().map(id -> id instanceof Long ? (Long) id : Long.parseLong(id.toString())).toList();
        if (!lids.isEmpty()) {
            dictDataRepository.deleteAllById(lids);
        }
        return true;
    }

    @Override
    public PageData<SysDictDataVO> page(Map<String, Object> params) {
        Pageable pageable = JpaPageUtils.toPageable(params, "sort", true);
        Page<SysDictDataEntity> page = dictDataRepository.findAll(buildListSpec(params), pageable);
        PageData<SysDictDataVO> pageData = JpaPageUtils.toPageData(page, SysDictDataVO.class);
        setUserName(pageData.getList());
        return pageData;
    }

    private Specification<SysDictDataEntity> buildListSpec(Map<String, Object> params) {
        String dictTypeIdStr = (String) params.get("dictTypeId");
        String dictLabel = (String) params.get("dictLabel");
        String dictValue = (String) params.get("dictValue");
        Long dictTypeId = Long.parseLong(dictTypeIdStr);
        return (root, query, cb) -> {
            List<Predicate> ps = new ArrayList<>();
            ps.add(cb.equal(root.get("dictTypeId"), dictTypeId));
            if (StringUtils.isNotBlank(dictLabel)) {
                ps.add(cb.like(root.get("dictLabel"), "%" + dictLabel + "%"));
            }
            if (StringUtils.isNotBlank(dictValue)) {
                ps.add(cb.like(root.get("dictValue"), "%" + dictValue + "%"));
            }
            return cb.and(ps.toArray(Predicate[]::new));
        };
    }

    @Override
    public SysDictDataVO get(Long id) {
        SysDictDataEntity entity = dictDataRepository.findById(id).orElse(null);
        return ConvertUtils.sourceToTarget(entity, SysDictDataVO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void save(SysDictDataDTO dto) {
        checkDictLabelUnique(dto.getDictTypeId(), dto.getDictLabel(), null);
        SysDictDataEntity entity = ConvertUtils.sourceToTarget(dto, SysDictDataEntity.class);
        insert(entity);
        String dictType = dictTypeRepository.findDictTypeById(dto.getDictTypeId()).orElse(null);
        if (dictType != null) {
            redisUtils.delete(RedisKeys.getDictDataByTypeKey(dictType));
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(SysDictDataDTO dto) {
        checkDictLabelUnique(dto.getDictTypeId(), dto.getDictLabel(), String.valueOf(dto.getId()));
        SysDictDataEntity entity = ConvertUtils.sourceToTarget(dto, SysDictDataEntity.class);
        updateById(entity);
        String dictType = dictTypeRepository.findDictTypeById(dto.getDictTypeId()).orElse(null);
        if (dictType != null) {
            redisUtils.delete(RedisKeys.getDictDataByTypeKey(dictType));
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(Long[] ids) {
        List<Long> idList = Arrays.asList(ids);
        if (ToolUtil.isNotEmpty(idList)) {
            List<String> dictTypeList = Optional.ofNullable(dictDataRepository.findDictTypesByDataIds(idList))
                    .orElseGet(ArrayList::new);
            List<String> redisKeyList = new ArrayList<>();
            dictTypeList.forEach(dictType -> redisKeyList.add(RedisKeys.getDictDataByTypeKey(dictType)));
            if (ToolUtil.isNotEmpty(redisKeyList)) {
                redisUtils.delete(redisKeyList);
            }
            deleteBatchIds(idList);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteByTypeId(Long dictTypeId) {
        dictDataRepository.deleteByDictTypeId(dictTypeId);
    }

    private void setUserName(List<SysDictDataVO> sysDictDataList) {
        Set<Long> userIds = sysDictDataList.stream().flatMap(vo -> Stream.of(vo.getCreator(), vo.getUpdater()))
                .filter(Objects::nonNull).collect(Collectors.toSet());
        if (!userIds.isEmpty()) {
            List<SysUserEntity> sysUserEntities = sysUserRepository.findAllById(userIds);
            Map<Long, String> userNameMap = sysUserEntities.stream().collect(Collectors.toMap(SysUserEntity::getId,
                    SysUserEntity::getUsername, (existing, replacement) -> existing));
            sysDictDataList.forEach(vo -> {
                vo.setCreatorName(userNameMap.get(vo.getCreator()));
                vo.setUpdaterName(userNameMap.get(vo.getUpdater()));
            });
        }
    }

    /**
     * Same rule as legacy MyBatis: duplicate check on {@code dict_label} (param historically named dictValue).
     */
    private void checkDictLabelUnique(Long dictTypeId, String dictLabel, String excludeId) {
        Long ex = StringUtils.isNotBlank(excludeId) ? Long.parseLong(excludeId) : null;
        if (dictDataRepository.existsDuplicateLabel(dictTypeId, dictLabel, ex)) {
            throw new RenException(ErrorCode.DICT_LABEL_DUPLICATE);
        }
    }

    @Override
    public List<SysDictDataItem> getDictDataByType(String dictType) {
        if (StringUtils.isBlank(dictType)) {
            return null;
        }
        String key = RedisKeys.getDictDataByTypeKey(dictType);
        @SuppressWarnings("unchecked")
        List<SysDictDataItem> cachedData = (List<SysDictDataItem>) redisUtils.get(key);
        if (cachedData != null) {
            return cachedData;
        }
        List<SysDictDataItem> data = dictDataRepository.findDictDataItemsByDictType(dictType);
        if (data != null) {
            redisUtils.set(key, data);
        }
        return data;
    }
}
