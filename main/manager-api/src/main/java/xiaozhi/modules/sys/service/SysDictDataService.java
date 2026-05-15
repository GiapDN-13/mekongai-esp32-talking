package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysDictDataDTO;
import xiaozhi.modules.sys.entity.SysDictDataEntity;
import xiaozhi.modules.sys.vo.SysDictDataItem;
import xiaozhi.modules.sys.vo.SysDictDataVO;

/**
 * Dictionary data (label/value rows under a type).
 */
public interface SysDictDataService extends BaseService<SysDictDataEntity> {

    /**
     * Paginated dictionary rows (typically scoped by type id).
     *
     * @param params query including pagination and filters
     * @return page of rows
     */
    PageData<SysDictDataVO> page(Map<String, Object> params);

    /**
     * Load one row by id.
     *
     * @param id row id
     * @return view object or null
     */
    SysDictDataVO get(Long id);

    /**
     * Create a dictionary row.
     *
     * @param dto payload
     */
    void save(SysDictDataDTO dto);

    /**
     * Update an existing row.
     *
     * @param dto payload
     */
    void update(SysDictDataDTO dto);

    /**
     * Delete rows by ids.
     *
     * @param ids row ids
     */
    void delete(Long[] ids);

    /**
     * Delete all rows for a dictionary type.
     *
     * @param dictTypeId owning type id
     */
    void deleteByTypeId(Long dictTypeId);

    /**
     * List lightweight entries for a type code (for dropdowns, etc.).
     *
     * @param dictType type code
     * @return label/value pairs
     */
    List<SysDictDataItem> getDictDataByType(String dictType);

}