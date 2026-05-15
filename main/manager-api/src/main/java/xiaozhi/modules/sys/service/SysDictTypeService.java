package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysDictTypeDTO;
import xiaozhi.modules.sys.entity.SysDictTypeEntity;
import xiaozhi.modules.sys.vo.SysDictTypeVO;

/**
 * Dictionary type (metadata for a set of data rows).
 */
public interface SysDictTypeService extends BaseService<SysDictTypeEntity> {

    /**
     * Paginated dictionary types.
     *
     * @param params query including pagination and filters
     * @return page of types
     */
    PageData<SysDictTypeVO> page(Map<String, Object> params);

    /**
     * Load one type by id.
     *
     * @param id dictionary type id
     * @return view object or null
     */
    SysDictTypeVO get(Long id);

    /**
     * Create a dictionary type.
     *
     * @param dto payload
     */
    void save(SysDictTypeDTO dto);

    /**
     * Update an existing dictionary type.
     *
     * @param dto payload
     */
    void update(SysDictTypeDTO dto);

    /**
     * Delete types by ids.
     *
     * @param ids type ids
     */
    void delete(Long[] ids);

    /**
     * List types matching optional filters.
     *
     * @return list of types
     */
    List<SysDictTypeVO> list(Map<String, Object> params);
}