package xiaozhi.common.redis;

/**
 * Centralized Redis key builders.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
public class RedisKeys {
    /**
     * System parameters cache key.
     */
    public static String getSysParamsKey() {
        return "sys:params";
    }

    /**
     * Image captcha key.
     */
    public static String getCaptchaKey(String uuid) {
        return "sys:captcha:" + uuid;
    }

    /**
     * Unregistered-device captcha key.
     */
    public static String getDeviceCaptchaKey(String captcha) {
        return "sys:device:captcha:" + captcha;
    }

    /**
     * Username lookup by user id.
     */
    public static String getUserIdKey(Long userid) {
        return "sys:username:id:" + userid;
    }

    /**
     * Model display name by model id.
     */
    public static String getModelNameById(String id) {
        return "model:name:" + id;
    }

    /**
     * Model config payload by model id.
     */
    public static String getModelConfigById(String id) {
        return "model:data:" + id;
    }

    /**
     * TTS voice (timbre) name by id.
     */
    public static String getTimbreNameById(String id) {
        return "timbre:name:" + id;
    }

    /**
     * Device count per agent.
     */
    public static String getAgentDeviceCountById(String id) {
        return "agent:device:count:" + id;
    }

    /**
     * Last device connection time per agent.
     */
    public static String getAgentDeviceLastConnectedAtById(String id) {
        return "agent:device:lastConnected:" + id;
    }

    /**
     * Server-side config cache.
     */
    public static String getServerConfigKey() {
        return "server:config";
    }

    /**
     * Timbre detail cache by id.
     */
    public static String getTimbreDetailsKey(String id) {
        return "timbre:details:" + id;
    }

    /**
     * Application version key.
     */
    public static String getVersionKey() {
        return "sys:version";
    }

    /**
     * OTA firmware id by upload session uuid.
     */
    public static String getOtaIdKey(String uuid) {
        return "ota:id:" + uuid;
    }

    /**
     * OTA firmware download counter.
     */
    public static String getOtaDownloadCountKey(String uuid) {
        return "ota:download:count:" + uuid;
    }

    /**
     * Dictionary rows by type code.
     */
    public static String getDictDataByTypeKey(String dictType) {
        return "sys:dict:data:" + dictType;
    }

    /**
     * Agent chat audio id mapping.
     */
    public static String getAgentAudioIdKey(String uuid) {
        return "agent:audio:id:" + uuid;
    }

    /**
     * SMS verification code for a phone number.
     */
    public static String getSMSValidateCodeKey(String phone) {
        return "sms:Validate:Code:" + phone;
    }

    /**
     * Last SMS send timestamp per phone.
     */
    public static String getSMSLastSendTimeKey(String phone) {
        return "sms:Validate:Code:" + phone + ":last_send_time";
    }

    /**
     * Daily SMS send count per phone.
     */
    public static String getSMSTodayCountKey(String phone) {
        return "sms:Validate:Code:" + phone + ":today_count";
    }

    /**
     * Chat history UUID mapping.
     */
    public static String getChatHistoryKey(String uuid) {
        return "agent:chat:history:" + uuid;
    }

    /**
     * Voice-clone upload audio id mapping.
     */
    public static String getVoiceCloneAudioIdKey(String uuid) {
        return "voiceClone:audio:id:" + uuid;
    }

    /**
     * Knowledge base cache by dataset id.
     */
    public static String getKnowledgeBaseCacheKey(String datasetId) {
        return "knowledge:base:" + datasetId;
    }

    /**
     * Temporary device registration marker.
     */
    public static String getTmpRegisterMacKey(String deviceId) {
        return "tmp_register_mac:" + deviceId;
    }

    /**
     * OTA activation code binding.
     */
    public static String getOtaActivationCode(String activationCode) {
        return "ota:activation:code:" + activationCode;
    }

    /**
     * OTA device activation payload (MAC-related).
     */
    public static String getOtaDeviceActivationInfo(String deviceId) {
        return "ota:activation:data:" + deviceId;
    }

    /**
     * OTA upload attempt counter per user.
     */
    public static String getOtaUploadCountKey(Long username) {
        return "ota:upload:count:" + username;
    }
}
