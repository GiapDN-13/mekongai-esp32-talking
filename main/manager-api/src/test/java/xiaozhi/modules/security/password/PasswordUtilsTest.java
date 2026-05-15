package xiaozhi.modules.security.password;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for PasswordUtils — BCrypt hash and verify.
 */
class PasswordUtilsTest {

    @Test
    void encode_producesNonNullHash() {
        String hash = PasswordUtils.encode("admin");
        assertNotNull(hash);
        assertFalse(hash.isEmpty());
    }

    @Test
    void encode_hashStartsWithBcryptPrefix() {
        String hash = PasswordUtils.encode("password123");
        assertTrue(hash.startsWith("$2"), "BCrypt hash should start with $2");
    }

    @Test
    void matches_correctPasswordReturnsTrue() {
        String raw = "mySecretPassword";
        String hash = PasswordUtils.encode(raw);
        assertTrue(PasswordUtils.matches(raw, hash));
    }

    @Test
    void matches_wrongPasswordReturnsFalse() {
        String hash = PasswordUtils.encode("correct");
        assertFalse(PasswordUtils.matches("wrong", hash));
    }

    @Test
    void encode_samePlaintextProducesDifferentHashes() {
        String raw = "samePassword";
        String hash1 = PasswordUtils.encode(raw);
        String hash2 = PasswordUtils.encode(raw);
        assertNotEquals(hash1, hash2, "BCrypt should produce different hashes due to random salt");
        assertTrue(PasswordUtils.matches(raw, hash1));
        assertTrue(PasswordUtils.matches(raw, hash2));
    }

    @Test
    void encode_handlesEmptyString() {
        String hash = PasswordUtils.encode("");
        assertNotNull(hash);
        assertTrue(PasswordUtils.matches("", hash));
        assertFalse(PasswordUtils.matches("notempty", hash));
    }

    @Test
    void encode_handlesUnicodeCharacters() {
        String raw = "mật_khẩu_Việt_Nam_🔑";
        String hash = PasswordUtils.encode(raw);
        assertTrue(PasswordUtils.matches(raw, hash));
    }
}
