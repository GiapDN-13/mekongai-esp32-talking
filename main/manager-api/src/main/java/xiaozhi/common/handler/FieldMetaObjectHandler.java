package xiaozhi.common.handler;

import java.util.Date;

import org.apache.ibatis.reflection.MetaObject;
import org.springframework.stereotype.Component;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;

import xiaozhi.common.constant.Constant;
import xiaozhi.common.user.UserDetail;
import xiaozhi.modules.security.user.SecurityUser;

/**
 * MyBatis-Plus auto-fill for audit columns (creator, timestamps, etc.).
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Component
public class FieldMetaObjectHandler implements MetaObjectHandler {
    private final static String CREATE_DATE = "createDate";
    private final static String CREATOR = "creator";
    private final static String UPDATE_DATE = "updateDate";
    private final static String UPDATER = "updater";

    private final static String DATA_OPERATION = "dataOperation";

    @Override
    public void insertFill(MetaObject metaObject) {
        UserDetail user = SecurityUser.getUser();
        Date date = new Date();

        // Creator
        strictInsertFill(metaObject, CREATOR, Long.class, user.getId());
        // Created time — supports createDate or createdAt
        if (metaObject.hasSetter(CREATE_DATE)) {
            strictInsertFill(metaObject, CREATE_DATE, Date.class, date);
        }
        if (metaObject.hasSetter("createdAt")) {
            strictInsertFill(metaObject, "createdAt", Date.class, date);
        }

        // Updater (initial same as creator on insert)
        strictInsertFill(metaObject, UPDATER, Long.class, user.getId());
        // Updated time — supports updateDate or updatedAt
        if (metaObject.hasSetter(UPDATE_DATE)) {
            strictInsertFill(metaObject, UPDATE_DATE, Date.class, date);
        }
        if (metaObject.hasSetter("updatedAt")) {
            strictInsertFill(metaObject, "updatedAt", Date.class, date);
        }

        // Logical data-operation marker
        strictInsertFill(metaObject, DATA_OPERATION, String.class, Constant.DataOperation.INSERT.getValue());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        Date date = new Date();

        // Updater
        strictUpdateFill(metaObject, UPDATER, Long.class, SecurityUser.getUserId());
        // Updated time — supports updateDate or updatedAt
        if (metaObject.hasSetter(UPDATE_DATE)) {
            strictUpdateFill(metaObject, UPDATE_DATE, Date.class, date);
        }
        if (metaObject.hasSetter("updatedAt")) {
            strictUpdateFill(metaObject, "updatedAt", Date.class, date);
        }

        // Logical data-operation marker
        strictInsertFill(metaObject, DATA_OPERATION, String.class, Constant.DataOperation.UPDATE.getValue());
    }
}