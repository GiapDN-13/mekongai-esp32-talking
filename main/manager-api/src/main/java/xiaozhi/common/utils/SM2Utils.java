package xiaozhi.common.utils;

import org.bouncycastle.asn1.gm.GMNamedCurves;
import org.bouncycastle.asn1.x9.X9ECParameters;
import org.bouncycastle.crypto.engines.SM2Engine;
import org.bouncycastle.crypto.params.ECDomainParameters;
import org.bouncycastle.crypto.params.ECPrivateKeyParameters;
import org.bouncycastle.crypto.params.ECPublicKeyParameters;
import org.bouncycastle.crypto.params.ParametersWithRandom;
import org.bouncycastle.jcajce.provider.asymmetric.ec.BCECPrivateKey;
import org.bouncycastle.jcajce.provider.asymmetric.ec.BCECPublicKey;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.math.ec.ECPoint;
import org.bouncycastle.util.encoders.Hex;

import java.math.BigInteger;
import java.security.*;
import java.security.spec.ECGenParameterSpec;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * SM2 crypto (hex-encoded keys/ciphertext; compatible with chancheng-archive-service).
 */
public class SM2Utils {

    /**
     * Map key for public key hex.
     */
    public static final String KEY_PUBLIC_KEY = "publicKey";
    /**
     * Map key for private key hex.
     */
    public static final String KEY_PRIVATE_KEY = "privateKey";

    static {
        Security.addProvider(new BouncyCastleProvider());
    }

    /**
     * SM2 encrypt (UTF-8 plaintext → hex ciphertext).
     *
     * @param publicKey hex-encoded public key (02/03 compressed or 04 uncompressed)
     * @param data      plaintext
     * @return hex ciphertext
     */
    public static String encrypt(String publicKey, String data) {
        try {
            X9ECParameters sm2ECParameters = GMNamedCurves.getByName("sm2p256v1");
            ECDomainParameters domainParameters = new ECDomainParameters(sm2ECParameters.getCurve(), sm2ECParameters.getG(), sm2ECParameters.getN());
            ECPoint pukPoint = sm2ECParameters.getCurve().decodePoint(Hex.decode(publicKey));
            ECPublicKeyParameters publicKeyParameters = new ECPublicKeyParameters(pukPoint, domainParameters);

            SM2Engine sm2Engine = new SM2Engine(SM2Engine.Mode.C1C3C2);
            sm2Engine.init(true, new ParametersWithRandom(publicKeyParameters, new SecureRandom()));

            byte[] in = data.getBytes(StandardCharsets.UTF_8);
            byte[] arrayOfBytes = sm2Engine.processBlock(in, 0, in.length);
            return Hex.toHexString(arrayOfBytes);
        } catch (Exception e) {
            throw new RuntimeException("SM2 encrypt failed", e);
        }
    }

    /**
     * SM2 decrypt (hex ciphertext → UTF-8 plaintext).
     *
     * @param privateKey hex private key scalar
     * @param cipherData hex ciphertext (prefix 04 added if missing)
     */
    public static String decrypt(String privateKey, String cipherData) {
        try {
            if (!cipherData.startsWith("04")) {
                cipherData = "04" + cipherData;
            }
            byte[] cipherDataByte = Hex.decode(cipherData);
            BigInteger privateKeyD = new BigInteger(privateKey, 16);
            X9ECParameters sm2ECParameters = GMNamedCurves.getByName("sm2p256v1");
            ECDomainParameters domainParameters = new ECDomainParameters(sm2ECParameters.getCurve(), sm2ECParameters.getG(), sm2ECParameters.getN());
            ECPrivateKeyParameters privateKeyParameters = new ECPrivateKeyParameters(privateKeyD, domainParameters);

            SM2Engine sm2Engine = new SM2Engine(SM2Engine.Mode.C1C3C2);
            sm2Engine.init(false, privateKeyParameters);

            byte[] arrayOfBytes = sm2Engine.processBlock(cipherDataByte, 0, cipherDataByte.length);
            return new String(arrayOfBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("SM2 decrypt failed", e);
        }
    }

    /**
     * Generate a new SM2 key pair (hex strings).
     */
    public static Map<String, String> createKey() {
        try {
            ECGenParameterSpec sm2Spec = new ECGenParameterSpec("sm2p256v1");
            KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC", new BouncyCastleProvider());
            kpg.initialize(sm2Spec);
            KeyPair keyPair = kpg.generateKeyPair();
            PublicKey publicKey = keyPair.getPublic();
            BCECPublicKey p = (BCECPublicKey) publicKey;
            PrivateKey privateKey = keyPair.getPrivate();
            BCECPrivateKey s = (BCECPrivateKey) privateKey;
            
            Map<String, String> result = new HashMap<>();
            result.put(KEY_PUBLIC_KEY, Hex.toHexString(p.getQ().getEncoded(false)));
            result.put(KEY_PRIVATE_KEY, Hex.toHexString(s.getD().toByteArray()));
            return result;
        } catch (Exception e) {
            throw new RuntimeException("SM2 key generation failed", e);
        }
    }


}