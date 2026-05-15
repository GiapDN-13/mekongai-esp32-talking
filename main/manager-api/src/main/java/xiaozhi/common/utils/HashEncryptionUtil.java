package xiaozhi.common.utils;

import lombok.extern.slf4j.Slf4j;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Message-digest helpers (MD5, etc.).
 * @author zjy
 */
@Slf4j
public class HashEncryptionUtil {
    /**
     * MD5 hex digest.
     *
     * @param context input string
     */
    public static String Md5hexDigest(String context){
        return hexDigest(context,"MD5");
    }

    /**
     * Hex digest with the given JCA algorithm name.
     */
   public static String hexDigest(String context,String algorithm ){
       MessageDigest md = null;
       try {
           md = MessageDigest.getInstance(algorithm);
       } catch (NoSuchAlgorithmException e) {
           log.error("Unsupported digest algorithm: {}", algorithm);
           throw new RuntimeException("Digest failed: JVM has no provider for " + algorithm, e);
       }
       byte[] messageDigest = md.digest(context.getBytes());
       StringBuilder hexString = new StringBuilder();
       for (byte b : messageDigest) {
           String hex = Integer.toHexString(0xFF & b);
           if (hex.length() == 1) {
               hexString.append('0');
           }
           hexString.append(hex);
       }
       return hexString.toString();
   }

}
