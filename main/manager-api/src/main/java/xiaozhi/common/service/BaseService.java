package xiaozhi.common.service;

import java.io.Serializable;
import java.util.Collection;

import com.baomidou.mybatisplus.core.conditions.Wrapper;

/**
 * Base MyBatis-Plus service operations; module services typically extend this.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
public interface BaseService<T> {
    Class<T> currentModelClass();

    /**
     * Insert one row (field-level insert, strategy-driven).
     *
     * @param entity row to persist
     */
    boolean insert(T entity);

    /**
     * Batch insert (not supported on Oracle / SQL Server by MyBatis-Plus default).
     *
     * @param entityList rows to persist
     */
    boolean insertBatch(Collection<T> entityList);

    /**
     * Batch insert with explicit batch size (not supported on Oracle / SQL Server by default).
     *
     * @param entityList rows to persist
     * @param batchSize  rows per JDBC batch
     */
    boolean insertBatch(Collection<T> entityList, int batchSize);

    /**
     * Update by primary key.
     *
     * @param entity row with id set
     */
    boolean updateById(T entity);

    /**
     * Update rows matching {@code updateWrapper}.
     *
     * @param entity        partial row / set clause source
     * @param updateWrapper condition wrapper
     *                      {@link com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper}
     */
    boolean update(T entity, Wrapper<T> updateWrapper);

    /**
     * Batch update by id.
     *
     * @param entityList rows to update
     */
    boolean updateBatchById(Collection<T> entityList);

    /**
     * Batch update by id with JDBC batch size.
     *
     * @param entityList rows to update
     * @param batchSize  batch size
     */
    boolean updateBatchById(Collection<T> entityList, int batchSize);

    /**
     * Select by primary key.
     *
     * @param id primary key
     */
    T selectById(Serializable id);

    /**
     * Delete by primary key.
     *
     * @param id primary key
     */
    boolean deleteById(Serializable id);

    /**
     * Delete by primary keys.
     *
     * @param idList primary keys
     */
    boolean deleteBatchIds(Collection<? extends Serializable> idList);
}
