package com.easysub.app;

import static org.junit.Assert.*;
import android.content.Context;
import android.content.Intent;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.File;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class NativeStorageTest {
    @Test public void coldLaunchLoadsAndAtomicallySavesEncryptedDatabase() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        File database = new File(context.getNoBackupFilesDir(), "local-v1.enc");
        long before = database.exists() ? database.lastModified() : 0;
        Intent intent = new Intent(context, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        context.startActivity(intent);
        long deadline = System.currentTimeMillis() + 15000;
        while ((!database.exists() || database.lastModified() == before) && System.currentTimeMillis() < deadline) Thread.sleep(100);
        assertTrue("Startup must save the local database", database.exists());
        assertTrue("Existing data must load successfully before a new save", database.lastModified() > before);
        byte[] bytes = Files.readAllBytes(database.toPath());
        assertTrue(bytes.length > 29);
        assertEquals(1, bytes[0]);
        String raw = new String(bytes, StandardCharsets.UTF_8);
        assertFalse("Business data must not be stored as plaintext", raw.contains("\"subscriptions\""));
        assertFalse("Tokens must not be stored as plaintext", raw.contains("\"access_token\""));
    }
}
