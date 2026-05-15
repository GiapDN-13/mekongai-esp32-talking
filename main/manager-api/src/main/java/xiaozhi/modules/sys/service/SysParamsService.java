package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.entity.SysParamsEntity;

/**
 * System parameters (key-value configuration).
 */
public interface SysParamsService extends BaseService<SysParamsEntity> {

    PageData<SysParamsDTO> page(Map<String, Object> params);

    List<SysParamsDTO> list(Map<String, Object> params);

    SysParamsDTO get(Long id);

    void save(SysParamsDTO dto);

    void update(SysParamsDTO dto);

    void delete(String[] ids);

    /**
     * Load raw string value by parameter code.
     *
     * @param paramCode  parameter code
     * @param fromCache  when true, read through cache layer
     */
    String getValue(String paramCode, Boolean fromCache);

    /**
     * Deserialize parameter value to {@code T}.
     *
     * @param paramCode parameter code
     * @param clazz     target type
     */
    <T> T getValueObject(String paramCode, Class<T> clazz);

    /**
     * Update stored value for a parameter code.
     *
     * @param paramCode  parameter code
     * @param paramValue new value
     */
    int updateValueByCode(String paramCode, String paramValue);

    /**
     * Ensure server secret parameter exists (bootstrap).
     */
    void initServerSecret();
}
