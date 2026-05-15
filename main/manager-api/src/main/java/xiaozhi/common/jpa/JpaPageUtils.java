package xiaozhi.common.jpa;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

import com.baomidou.mybatisplus.core.toolkit.CollectionUtils;
import com.baomidou.mybatisplus.core.toolkit.StringUtils;

import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;

/**
 * Map-based pagination (same keys as {@link xiaozhi.common.service.impl.BaseServiceImpl}) → Spring Data {@link Pageable}.
 */
public final class JpaPageUtils {

    private JpaPageUtils() {
    }

    /**
     * @param defaultOrderField entity property name; optional
     */
    public static Pageable toPageable(Map<String, Object> params, String defaultOrderField, boolean defaultAsc) {
        long curPage = 1L;
        long limit = 10L;
        if (params.get(Constant.PAGE) != null) {
            curPage = Long.parseLong((String) params.get(Constant.PAGE));
        }
        if (params.get(Constant.LIMIT) != null) {
            limit = Long.parseLong((String) params.get(Constant.LIMIT));
        }
        int pageIndex = (int) Math.max(0L, curPage - 1);

        Object orderField = params.get(Constant.ORDER_FIELD);
        String order = (String) params.get(Constant.ORDER);

        List<String> orderFields = new ArrayList<>();
        if (orderField instanceof String s && StringUtils.isNotBlank(s)) {
            orderFields.add(s);
        } else if (orderField instanceof List<?> list) {
            for (Object o : list) {
                if (o != null) {
                    orderFields.add(o.toString());
                }
            }
        }

        Sort sort;
        if (CollectionUtils.isNotEmpty(orderFields)) {
            Sort.Direction dir = StringUtils.isNotBlank(order) && Constant.ASC.equalsIgnoreCase(order)
                    ? Sort.Direction.ASC
                    : Sort.Direction.DESC;
            sort = Sort.by(dir, orderFields.toArray(new String[0]));
        } else if (StringUtils.isNotBlank(defaultOrderField)) {
            sort = defaultAsc ? Sort.by(defaultOrderField).ascending() : Sort.by(defaultOrderField).descending();
        } else {
            sort = Sort.unsorted();
        }

        return PageRequest.of(pageIndex, (int) limit, sort);
    }

    public static <T, D> PageData<D> toPageData(Page<T> page, Class<D> dtoClass) {
        List<D> list = ConvertUtils.sourceToTarget(page.getContent(), dtoClass);
        return new PageData<>(list, page.getTotalElements());
    }
}
