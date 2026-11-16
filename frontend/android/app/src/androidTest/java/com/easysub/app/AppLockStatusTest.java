package com.easysub.app;
import static org.junit.Assert.*;
import android.app.KeyguardManager;
import android.content.Context;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import com.getcapacitor.JSObject;
import org.junit.Test;
import org.junit.runner.RunWith;
@RunWith(AndroidJUnit4.class)
public class AppLockStatusTest {
    @Test public void statusReportsDeviceCapabilitiesWithoutChangingSettings() {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        JSObject status = AppLockPlugin.statusFor(context);
        assertNotNull(status.getBool("enabled"));
        assertNotNull(status.getBool("available"));
        assertTrue(AppLockPolicy.validMinutes(status.getInteger("relockMinutes")));
        if (!context.getSystemService(KeyguardManager.class).isDeviceSecure()) {
            assertFalse(status.getBool("available"));assertEquals("NO_DEVICE_CREDENTIAL", status.getString("reason"));
        }
    }
}
