declare module 'sm-crypto' {
  export const sm2: {
    doEncrypt(data: string, publicKey: string, cipherMode?: number): string;
    doDecrypt(data: string, privateKey: string, cipherMode?: number): string;
    generateKeyPairHex(): { publicKey: string; privateKey: string };
  };
}
