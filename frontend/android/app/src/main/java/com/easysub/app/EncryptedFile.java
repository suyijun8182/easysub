package com.easysub.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * AES-256-GCM files in noBackupFilesDir, keyed by the app's Android Keystore key.
 * Format: version byte 1, 12-byte IV, ciphertext with tag. Writes go through AtomicFile.
 */
final class EncryptedFile {
    static final String ALIAS = "easysub.local.v1";
    static final int MAX_BYTES = 50 * 1024 * 1024;
    private static final Object LOCK = new Object();
    private EncryptedFile() {}

    private static SecretKey key(boolean create) throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (store.containsAlias(ALIAS)) return (SecretKey) store.getKey(ALIAS, null);
        if (!create) throw new IllegalStateException("Local encryption key is unavailable");
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
        return generator.generateKey();
    }
    private static AtomicFile file(Context context, String name) { return new AtomicFile(new File(context.getNoBackupFilesDir(), name)); }

    /** Returns null when the file does not exist; throws when it exists but cannot be decrypted. */
    static String read(Context context, String name) throws Exception {
        synchronized (LOCK) {
            AtomicFile file = file(context, name);
            if (!file.getBaseFile().exists() && !new File(file.getBaseFile() + ".bak").exists()) return null;
            byte[] bytes = file.readFully();
            if (bytes.length < 29 || bytes[0] != 1) throw new IllegalStateException("Invalid encrypted file");
            byte[] iv = new byte[12]; System.arraycopy(bytes, 1, iv, 0, 12);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.DECRYPT_MODE, key(false), new GCMParameterSpec(128, iv));
            return new String(cipher.doFinal(bytes, 13, bytes.length - 13), StandardCharsets.UTF_8);
        }
    }

    static void write(Context context, String name, String text) throws Exception {
        if (text == null || text.length() > MAX_BYTES) throw new IllegalArgumentException("Encrypted file size limit exceeded");
        synchronized (LOCK) {
            FileOutputStream stream = null; AtomicFile file = file(context, name);
            try {
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key(true));
                byte[] encrypted = cipher.doFinal(text.getBytes(StandardCharsets.UTF_8));
                byte[] bytes = ByteBuffer.allocate(13 + encrypted.length).put((byte) 1).put(cipher.getIV()).put(encrypted).array();
                stream = file.startWrite(); stream.write(bytes); file.finishWrite(stream); stream = null;
            } finally { if (stream != null) file.failWrite(stream); }
        }
    }

    static void delete(Context context, String name) { synchronized (LOCK) { file(context, name).delete(); } }

    /** Read-modify-write under the same lock as read/write, so concurrent updates are not lost. */
    interface Update { String apply(String current) throws Exception; }
    static void update(Context context, String name, Update update) throws Exception {
        synchronized (LOCK) {
            String next = update.apply(read(context, name));
            if (next == null) delete(context, name); else write(context, name, next);
        }
    }
}
