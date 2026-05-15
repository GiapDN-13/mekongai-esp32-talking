package xiaozhi.common.page;

import java.io.Serializable;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Paginated list wrapper.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Data
@Schema(description = "Paginated data")
public class PageData<T> implements Serializable {
    @Schema(description = "Total row count")
    private int total;

    @Schema(description = "Current page items")
    private List<T> list;

    /**
     * Build a page view.
     *
     * @param list  items for this page
     * @param total total matching rows
     */
    public PageData(List<T> list, long total) {
        this.list = list;
        this.total = (int) total;
    }
}