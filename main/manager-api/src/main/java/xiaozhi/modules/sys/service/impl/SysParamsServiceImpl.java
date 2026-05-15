package xiaozhi.modules.sys.service.impl;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.UUID;

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
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.jpa.JpaAuditHelper;
import xiaozhi.common.jpa.JpaPageUtils;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.common.utils.SM2Utils;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.entity.SysParamsEntity;
import xiaozhi.modules.sys.redis.SysParamsRedis;
import xiaozhi.modules.sys.repository.SysParamsRepository;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * {@link SysParamsService} backed by JPA and Redis cache.
 */
@RequiredArgsConstructor
@Service
public class SysParamsServiceImpl implements SysParamsService {

    private final SysParamsRepository sysParamsRepository;
    private final SysParamsRedis sysParamsRedis;

    @Override
    public Class<SysParamsEntity> currentModelClass() {
        return SysParamsEntity.class;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(SysParamsEntity entity) {
        JpaAuditHelper.fillInsert(entity);
        if (entity.getId() == null) {
            entity.setId(IdWorker.getId());
        }
        sysParamsRepository.save(entity);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysParamsEntity> entityList) {
        return insertBatch(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<SysParamsEntity> entityList, int batchSize) {
        List<SysParamsEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            List<SysParamsEntity> batch = list.subList(i, end);
            for (SysParamsEntity e : batch) {
                JpaAuditHelper.fillInsert(e);
                if (e.getId() == null) {
                    e.setId(IdWorker.getId());
                }
            }
            sysParamsRepository.saveAll(batch);
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(SysParamsEntity entity) {
        JpaAuditHelper.fillUpdate(entity);
        sysParamsRepository.save(entity);
        return true;
    }

    @Override
    public boolean update(SysParamsEntity entity, Wrapper<SysParamsEntity> updateWrapper) {
        throw new UnsupportedOperationException("SysParams: conditional MyBatis update is not supported; use save/update DTO APIs");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysParamsEntity> entityList) {
        return updateBatchById(entityList, 100);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<SysParamsEntity> entityList, int batchSize) {
        List<SysParamsEntity> list = new ArrayList<>(entityList);
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            for (SysParamsEntity e : list.subList(i, end)) {
                JpaAuditHelper.fillUpdate(e);
            }
            sysParamsRepository.saveAll(list.subList(i, end));
        }
        return true;
    }

    @Override
    public SysParamsEntity selectById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        return sysParamsRepository.findById(lid).orElse(null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteById(Serializable id) {
        Long lid = id instanceof Long ? (Long) id : Long.parseLong(id.toString());
        sysParamsRepository.deleteById(lid);
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteBatchIds(Collection<? extends Serializable> idList) {
        List<Long> lids = idList.stream().map(id -> id instanceof Long ? (Long) id : Long.parseLong(id.toString())).toList();
        if (!lids.isEmpty()) {
            sysParamsRepository.deleteAllById(lids);
        }
        return true;
    }

    @Override
    public PageData<SysParamsDTO> page(Map<String, Object> params) {
        Pageable pageable = JpaPageUtils.toPageable(params, null, false);
        String paramCode = (String) params.get("paramCode");
        Page<SysParamsEntity> page = sysParamsRepository.findAll(buildListSpec(paramCode), pageable);
        return JpaPageUtils.toPageData(page, SysParamsDTO.class);
    }

    @Override
    public List<SysParamsDTO> list(Map<String, Object> params) {
        String paramCode = (String) params.get("paramCode");
        List<SysParamsEntity> entityList = sysParamsRepository.findAll(buildListSpec(paramCode));
        return ConvertUtils.sourceToTarget(entityList, SysParamsDTO.class);
    }

    private Specification<SysParamsEntity> buildListSpec(String paramCode) {
        return (root, query, cb) -> {
            List<Predicate> ps = new ArrayList<>();
            ps.add(cb.equal(root.get("paramType"), 1));
            if (StringUtils.isNotBlank(paramCode)) {
                String like = "%" + paramCode + "%";
                ps.add(cb.or(
                        cb.like(root.get("paramCode"), like),
                        cb.like(root.get("remark"), like)));
            }
            return cb.and(ps.toArray(Predicate[]::new));
        };
    }

    @Override
    public SysParamsDTO get(Long id) {
        SysParamsEntity entity = sysParamsRepository.findById(id).orElse(null);
        return ConvertUtils.sourceToTarget(entity, SysParamsDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void save(SysParamsDTO dto) {
        validateParamValue(dto);
        SysParamsEntity entity = ConvertUtils.sourceToTarget(dto, SysParamsEntity.class);
        insert(entity);
        sysParamsRedis.set(entity.getParamCode(), entity.getParamValue());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(SysParamsDTO dto) {
        validateParamValue(dto);
        detectingSMSParameters(dto.getParamCode(), dto.getParamValue());

        SysParamsEntity entity = sysParamsRepository.findById(dto.getId()).orElse(null);
        if (entity == null) {
            throw new RenException(ErrorCode.DB_RECORD_NOT_FOUND);
        }
        entity.setParamCode(dto.getParamCode());
        entity.setParamValue(dto.getParamValue());
        entity.setValueType(dto.getValueType());
        entity.setRemark(dto.getRemark());

        updateById(entity);
        sysParamsRedis.set(entity.getParamCode(), entity.getParamValue());
    }

    private void validateParamValue(SysParamsDTO dto) {
        if (dto == null) {
            throw new RenException(ErrorCode.PARAM_VALUE_NULL);
        }
        if (StringUtils.isBlank(dto.getParamValue())) {
            throw new RenException(ErrorCode.PARAM_VALUE_NULL);
        }
        if (StringUtils.isBlank(dto.getValueType())) {
            throw new RenException(ErrorCode.PARAM_TYPE_NULL);
        }
        String valueType = dto.getValueType().toLowerCase();
        String paramValue = dto.getParamValue();
        switch (valueType) {
            case "string", "array" -> { /* ok */ }
            case "number" -> {
                try {
                    Double.parseDouble(paramValue);
                } catch (NumberFormatException e) {
                    throw new RenException(ErrorCode.PARAM_NUMBER_INVALID);
                }
            }
            case "boolean" -> {
                if (!"true".equalsIgnoreCase(paramValue) && !"false".equalsIgnoreCase(paramValue)) {
                    throw new RenException(ErrorCode.PARAM_BOOLEAN_INVALID);
                }
            }
            case "json" -> {
                try {
                    String trimmedValue = paramValue.trim();
                    if (!trimmedValue.startsWith("{") || !trimmedValue.endsWith("}")) {
                        throw new RenException(ErrorCode.PARAM_JSON_INVALID);
                    }
                    JsonUtils.parseObject(paramValue, Object.class);
                } catch (Exception e) {
                    throw new RenException(ErrorCode.PARAM_JSON_INVALID);
                }
            }
            default -> throw new RenException(ErrorCode.PARAM_TYPE_INVALID);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(String[] ids) {
        List<Long> longIds = Arrays.stream(ids).map(Long::parseLong).toList();
        List<String> paramCodeList = longIds.isEmpty() ? List.of() : sysParamsRepository.findParamCodesByIds(longIds);
        if (!paramCodeList.isEmpty()) {
            sysParamsRedis.delete(paramCodeList.toArray(new String[0]));
        }
        deleteBatchIds(longIds);
    }

    @Override
    public String getValue(String paramCode, Boolean fromCache) {
        String paramValue = null;
        if (Boolean.TRUE.equals(fromCache)) {
            paramValue = sysParamsRedis.get(paramCode);
            if (paramValue == null) {
                paramValue = sysParamsRepository.findParamValueByParamCode(paramCode).orElse(null);
                sysParamsRedis.set(paramCode, paramValue);
            }
        } else {
            paramValue = sysParamsRepository.findParamValueByParamCode(paramCode).orElse(null);
        }
        return paramValue;
    }

    @Override
    public <T> T getValueObject(String paramCode, Class<T> clazz) {
        String paramValue = getValue(paramCode, true);
        if (StringUtils.isNotBlank(paramValue)) {
            return JsonUtils.parseObject(paramValue, clazz);
        }
        try {
            return clazz.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int updateValueByCode(String paramCode, String paramValue) {
        int count = sysParamsRepository.updateValueByParamCode(paramCode, paramValue);
        sysParamsRedis.set(paramCode, paramValue);
        return count;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void initServerSecret() {
        String secretParam = getValue(Constant.SERVER_SECRET, false);
        if (StringUtils.isBlank(secretParam) || "null".equals(secretParam)) {
            String newSecret = UUID.randomUUID().toString();
            updateValueByCode(Constant.SERVER_SECRET, newSecret);
        }
        initSM2KeyPair();
    }

    private void initSM2KeyPair() {
        String publicKey = getValue(Constant.SM2_PUBLIC_KEY, false);
        String privateKey = getValue(Constant.SM2_PRIVATE_KEY, false);
        if (StringUtils.isBlank(publicKey) || StringUtils.isBlank(privateKey)
                || "null".equals(publicKey) || "null".equals(privateKey)) {
            Map<String, String> keyPair = SM2Utils.createKey();
            String newPublicKey = keyPair.get(SM2Utils.KEY_PUBLIC_KEY);
            String newPrivateKey = keyPair.get(SM2Utils.KEY_PRIVATE_KEY);
            updateValueByCode(Constant.SM2_PUBLIC_KEY, newPublicKey);
            updateValueByCode(Constant.SM2_PRIVATE_KEY, newPrivateKey);
        }
    }

    private boolean detectingSMSParameters(String paramCode, String paramValue) {
        if (!Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue().equals(paramCode)) {
            return true;
        }
        if ("false".equalsIgnoreCase(paramValue)) {
            return true;
        }
        ArrayList<String> list = new ArrayList<>();
        list.add(Constant.SysMSMParam.SERVER_SMS_MAX_SEND_COUNT.getValue());
        list.add(Constant.SysMSMParam.ALIYUN_SMS_ACCESS_KEY_ID.getValue());
        list.add(Constant.SysMSMParam.ALIYUN_SMS_ACCESS_KEY_SECRET.getValue());
        list.add(Constant.SysMSMParam.ALIYUN_SMS_SIGN_NAME.getValue());
        list.add(Constant.SysMSMParam.ALIYUN_SMS_SMS_CODE_TEMPLATE_CODE.getValue());
        StringBuilder str = new StringBuilder();
        list.forEach(item -> {
            if (!StringUtils.isNoneBlank(item)) {
                str.append(",").append(item);
            }
        });
        if (!str.isEmpty()) {
            String promptStr = "The following parameters must not be empty: %s";
            String substring = str.substring(1, str.length());
            throw new RenException(promptStr.formatted(substring));
        }
        return true;
    }

}
