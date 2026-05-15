package xiaozhi.common.utils;

import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.apache.commons.lang3.StringUtils;

import cn.hutool.json.JSONObject;

/**
 * Masking and equality checks for secret-like JSON fields.
 */
public class SensitiveDataUtils {

    // Known sensitive JSON keys (lowercase match)
    private static final Set<String> SENSITIVE_FIELDS = new HashSet<>(Arrays.asList(
            "api_key", "personal_access_token", "access_token", "token",
            "secret", "access_key_secret", "secret_key"));

    /** Whether the key name is treated as sensitive. */
    public static boolean isSensitiveField(String fieldName) {
        return StringUtils.isNotBlank(fieldName) && SENSITIVE_FIELDS.contains(fieldName.toLowerCase());
    }

    /** Mask middle of a string while keeping prefix/suffix. */
    public static String maskMiddle(String value) {
        if (StringUtils.isBlank(value) || value.length() == 1) {
            return value;
        }

        int length = value.length();
        if (length <= 8) {
            // Short: keep 2 + 2 chars
            return value.substring(0, 2) + "****" + value.substring(length - 2);
        } else {
            // Long: keep 4 + 4 chars
            int maskLength = length - 8;
            StringBuilder maskBuilder = new StringBuilder();
            for (int i = 0; i < maskLength; i++) {
                maskBuilder.append('*');
            }
            return value.substring(0, 4) + maskBuilder.toString() + value.substring(length - 4);
        }
    }

    /** Heuristic: masked values contain {@code ****}. */
    public static boolean isMaskedValue(String value) {
        if (StringUtils.isBlank(value)) {
            return false;
        }
        // Masked output uses a **** segment
        return value.contains("****");
    }

    /** Deep-copy JSON while masking sensitive string leaves. */
    public static JSONObject maskSensitiveFields(JSONObject jsonObject) {
        if (jsonObject == null) {
            return null;
        }

        JSONObject result = new JSONObject();

        for (String key : jsonObject.keySet()) {
            Object value = jsonObject.get(key);

            if (SENSITIVE_FIELDS.contains(key.toLowerCase()) && value instanceof String) {
                result.put(key, maskMiddle((String) value));
            } else if (value instanceof JSONObject) {
                result.put(key, maskSensitiveFields((JSONObject) value));
            } else {
                result.put(key, value);
            }
        }

        return result;
    }

    /**
     * Whether all known sensitive keys match between two JSON trees (by path + value).
     */
    public static boolean isSensitiveDataEqual(JSONObject original, JSONObject updated) {
        if (original == null && updated == null) {
            return true;
        }
        if (original == null || updated == null) {
            return false;
        }

        // Pairwise compare each sensitive key
        return compareSpecificSensitiveFields(original, updated, "api_key") &&
                compareSpecificSensitiveFields(original, updated, "personal_access_token") &&
                compareSpecificSensitiveFields(original, updated, "access_token") &&
                compareSpecificSensitiveFields(original, updated, "token") &&
                compareSpecificSensitiveFields(original, updated, "secret") &&
                compareSpecificSensitiveFields(original, updated, "access_key_secret") &&
                compareSpecificSensitiveFields(original, updated, "secret_key");
    }

    /** Compare one sensitive field name across two object trees. */
    private static boolean compareSpecificSensitiveFields(JSONObject original, JSONObject updated, String fieldName) {
        // Collect paths from original
        Map<String, String> originalFields = new HashMap<>();
        extractSpecificSensitiveField(original, originalFields, fieldName, "");

        // Collect paths from updated
        Map<String, String> updatedFields = new HashMap<>();
        extractSpecificSensitiveField(updated, updatedFields, fieldName, "");

        // Different cardinality => structural change
        if (originalFields.size() != updatedFields.size()) {
            return false;
        }

        // Same paths must have identical plaintext
        for (Map.Entry<String, String> entry : originalFields.entrySet()) {
            String key = entry.getKey();
            String originalValue = entry.getValue();
            String updatedValue = updatedFields.get(key);

            if (updatedValue == null || !updatedValue.equals(originalValue)) {
                return false;
            }
        }

        return true;
    }

    /** DFS collect string values for {@code targetFieldName}. */
    private static void extractSpecificSensitiveField(JSONObject jsonObject, Map<String, String> fieldsMap,
            String targetFieldName, String parentPath) {
        if (jsonObject == null) {
            return;
        }

        for (String key : jsonObject.keySet()) {
            String fullPath = parentPath.isEmpty() ? key : parentPath + "." + key;
            Object value = jsonObject.get(key);

            if (value instanceof JSONObject) {
                // Recurse into nested object
                extractSpecificSensitiveField((JSONObject) value, fieldsMap, targetFieldName, fullPath);
            } else if (value instanceof String && key.equalsIgnoreCase(targetFieldName)) {
                // Record path → value
                fieldsMap.put(fullPath, (String) value);
            }
        }
    }
}