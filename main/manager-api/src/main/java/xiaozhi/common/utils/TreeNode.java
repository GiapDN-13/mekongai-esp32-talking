package xiaozhi.common.utils;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

import lombok.Data;

/**
 * Minimal fields for {@link TreeUtils}; extend for domain-specific nodes.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Data
public class TreeNode<T> implements Serializable {

    /**
     * Primary key.
     */
    private Long id;
    /**
     * Parent id.
     */
    private Long pid;
    /**
     * Child nodes.
     */
    private List<T> children = new ArrayList<>();

}