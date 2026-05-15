package xiaozhi.modules.security.password;

/**
 * Password hashing and verification (BCrypt).
 * Copyright (c) Renren open source — all rights reserved.
 * Website: https://www.renren.io
 */
public class PasswordUtils {
    private static PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    /**
     * Hash a plaintext password.
     *
     * @param str raw password
     * @return encoded hash
     */
    public static String encode(String str) {
        return passwordEncoder.encode(str);
    }

    /**
     * Constant-time comparison of raw password to stored hash.
     *
     * @param str      raw password
     * @param password stored hash
     * @return true if they match
     */
    public static boolean matches(String str, String password) {
        return passwordEncoder.matches(str, password);
    }

    public static void main(String[] args) {
        String str = "admin";
        String password = encode(str);

        System.out.println(password);
        System.out.println(matches(str, password));
    }

}
