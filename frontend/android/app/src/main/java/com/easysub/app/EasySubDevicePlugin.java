package com.easysub.app;

import android.app.Activity;
import android.content.Intent;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

@CapacitorPlugin(name = "EasySubDevice")
public class EasySubDevicePlugin extends Plugin {
    private static final String ALIAS = "easysub.local.v1";
    private SecretKey key(boolean create) throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (store.containsAlias(ALIAS)) return (SecretKey) store.getKey(ALIAS, null);
        if (!create) throw new IllegalStateException("Local encryption key is unavailable");
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
        return generator.generateKey();
    }
    private AtomicFile file() { return new AtomicFile(new File(getContext().getNoBackupFilesDir(), "local-v1.enc")); }

    @PluginMethod public synchronized void load(PluginCall call) {
        try {
            AtomicFile file = file();
            if (!file.getBaseFile().exists() && !new File(file.getBaseFile() + ".bak").exists()) { call.resolve(new JSObject().put("json", (Object) null)); return; }
            byte[] bytes = file.readFully();
            if (bytes.length < 29 || bytes[0] != 1) throw new IllegalStateException("Invalid encrypted database");
            byte[] iv = new byte[12]; System.arraycopy(bytes, 1, iv, 0, 12);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.DECRYPT_MODE, key(false), new GCMParameterSpec(128, iv));
            String json = new String(cipher.doFinal(bytes, 13, bytes.length - 13), StandardCharsets.UTF_8);
            call.resolve(new JSObject().put("json", json));
        } catch (Exception error) { call.reject("Cannot decrypt local data. Existing files were kept.", "LOCAL_READ_FAILED"); }
    }
    @PluginMethod public synchronized void save(PluginCall call) {
        FileOutputStream stream = null; AtomicFile file = file();
        try {
            String json = call.getString("json");
            if (json == null || json.length() > 50 * 1024 * 1024) throw new IllegalArgumentException("Database size limit exceeded");
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key(true));
            byte[] encrypted = cipher.doFinal(json.getBytes(StandardCharsets.UTF_8));
            byte[] bytes = ByteBuffer.allocate(13 + encrypted.length).put((byte) 1).put(cipher.getIV()).put(encrypted).array();
            stream = file.startWrite(); stream.write(bytes); file.finishWrite(stream); stream = null;
            call.resolve();
        } catch (Exception error) { if (stream != null) file.failWrite(stream); call.reject("Cannot save local data", "LOCAL_WRITE_FAILED"); }
    }
    @PluginMethod public void exportFile(PluginCall call) {
        String text = call.getString("text"), name = call.getString("name");
        if (text == null || name == null) { call.reject("Missing file content"); return; }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
            .setType(call.getString("type", "application/json")).putExtra(Intent.EXTRA_TITLE, name);
        startActivityForResult(call, intent, "exportResult");
    }
    @ActivityCallback private void exportResult(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null || result.getData().getData() == null) {
            call.resolve(new JSObject().put("saved", false)); return;
        }
        try (OutputStream stream = getContext().getContentResolver().openOutputStream(result.getData().getData(), "wt")) {
            if (stream == null) throw new IllegalStateException("File unavailable");
            stream.write(call.getString("text", "").getBytes(StandardCharsets.UTF_8)); stream.flush();
            call.resolve(new JSObject().put("saved", true));
        } catch (Exception error) { call.reject("Cannot export file", "EXPORT_FAILED"); }
    }
}
