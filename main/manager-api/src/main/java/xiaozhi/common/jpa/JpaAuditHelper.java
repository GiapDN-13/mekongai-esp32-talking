package xiaozhi.common.jpa;

import java.lang.reflect.Method;
import java.util.Date;

import xiaozhi.common.entity.BaseEntity;
import xiaozhi.common.user.UserDetail;
import xiaozhi.modules.security.user.SecurityUser;

/**
 * Sets creator / dates / updater on entities (same intent as MyBatis {@code FieldMetaObjectHandler}).
 */
public final class JpaAuditHelper {

    private JpaAuditHelper() {
    }

    public static void fillInsert(BaseEntity entity) {
        UserDetail user = SecurityUser.getUser();
        Date now = new Date();
        entity.setCreator(user.getId());
        entity.setCreateDate(now);
        invokeOptionalSetter(entity, "setUpdater", Long.class, user.getId());
        invokeOptionalSetter(entity, "setUpdateDate", Date.class, now);
    }

    public static void fillUpdate(BaseEntity entity) {
        invokeOptionalSetter(entity, "setUpdater", Long.class, SecurityUser.getUser().getId());
        invokeOptionalSetter(entity, "setUpdateDate", Date.class, new Date());
    }

    private static void invokeOptionalSetter(BaseEntity entity, String name, Class<?> paramType, Object value) {
        try {
            Method m = entity.getClass().getMethod(name, paramType);
            m.invoke(entity, value);
        } catch (ReflectiveOperationException ignored) {
            // subclass without this setter
        }
    }
}
