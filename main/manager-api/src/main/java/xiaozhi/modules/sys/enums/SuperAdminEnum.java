package xiaozhi.modules.sys.enums;

/**
 * Whether a user is a super administrator (numeric flag).
 */
public enum SuperAdminEnum {
    YES(1),
    NO(0);

    private int value;

    SuperAdminEnum(int value) {
        this.value = value;
    }

    public int value() {
        return this.value;
    }
}