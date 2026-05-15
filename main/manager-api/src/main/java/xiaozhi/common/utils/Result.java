package xiaozhi.common.utils;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import xiaozhi.common.exception.ErrorCode;

/**
 * Standard API response envelope.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
@Data
@Schema(description = "API response")
public class Result<T> implements Serializable {

    /**
     * 0 = success; non-zero = error code.
     */
    @Schema(description = "0 = success; non-zero = error code")
    private int code = 0;
    /**
     * Human-readable message.
     */
    @Schema(description = "Message")
    private String msg = "success";
    /**
     * Response payload.
     */
    @Schema(description = "Payload")
    private T data;

    public Result<T> ok(T data) {
        this.setData(data);
        return this;
    }

    public Result<T> error() {
        this.code = ErrorCode.INTERNAL_SERVER_ERROR;
        this.msg = MessageUtils.getMessage(this.code);
        return this;
    }

    public Result<T> error(int code) {
        this.code = code;
        this.msg = MessageUtils.getMessage(this.code);
        return this;
    }

    public Result<T> error(int code, String msg) {
        this.code = code;
        this.msg = msg;
        return this;
    }

    public Result<T> error(String msg) {
        this.code = ErrorCode.INTERNAL_SERVER_ERROR;
        this.msg = msg;
        return this;
    }

}