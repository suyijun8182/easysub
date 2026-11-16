package com.easysub.app;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.net.Uri;
import android.provider.Settings;
import androidx.core.app.NotificationManagerCompat;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

@CapacitorPlugin(name = "EasySubDevice")
public class EasySubDevicePlugin extends Plugin {
    @PluginMethod public void notificationStatus(PluginCall call) {
        call.resolve(new JSObject().put("enabled", NotificationManagerCompat.from(getContext()).areNotificationsEnabled())
            .put("required", Build.VERSION.SDK_INT >= 33));
    }
    @PluginMethod public void openNotificationSettings(PluginCall call) {
        getActivity().runOnUiThread(() -> {
            try {
                Intent intent = Build.VERSION.SDK_INT >= 26
                    ? new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getContext().getPackageName())
                    : new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getContext().getPackageName()));
                getActivity().startActivity(intent); call.resolve();
            } catch (Exception error) {
                try {
                    getActivity().startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getContext().getPackageName())));
                    call.resolve();
                } catch (Exception fallback) { call.reject("Cannot open notification settings", "SETTINGS_UNAVAILABLE"); }
            }
        });
    }
    @PluginMethod public void load(PluginCall call) {
        try { call.resolve(new JSObject().put("json", (Object) EncryptedFile.read(getContext(), "local-v1.enc"))); }
        catch (Exception error) { call.reject("Cannot decrypt local data. Existing files were kept.", "LOCAL_READ_FAILED"); }
    }
    @PluginMethod public void save(PluginCall call) {
        try { EncryptedFile.write(getContext(), "local-v1.enc", call.getString("json")); call.resolve(); }
        catch (Exception error) { call.reject("Cannot save local data", "LOCAL_WRITE_FAILED"); }
    }

    // Background change check: see docs/android-native-background-check.md.
    @PluginMethod public void setBackgroundCheck(PluginCall call) {
        try {
            BackgroundCheck.Snapshot s = new BackgroundCheck.Snapshot();
            s.server = call.getString("server"); s.accessToken = call.getString("access_token", ""); s.refreshToken = call.getString("refresh_token", "");
            s.epoch = call.getString("epoch"); s.locale = call.getString("locale", "zh");
            Long cursor = BackgroundCheck.cursor(call.getData().opt("cursor"));
            if (s.server == null || s.epoch == null || cursor == null || !BackgroundCheck.safeServer(s.server)) { call.reject("Invalid background check snapshot", "INVALID_ARGUMENT"); return; }
            s.cursor = cursor;
            BackgroundCheckStore.save(getContext(), s);
            BackgroundCheckScheduler.sync(getContext());
            call.resolve();
        } catch (Exception error) { call.reject("Cannot save background check snapshot", "LOCAL_WRITE_FAILED"); }
    }
    @PluginMethod public void clearBackgroundCheck(PluginCall call) {
        BackgroundCheckStore.delete(getContext());
        BackgroundCheckScheduler.cancel(getContext());
        call.resolve();
    }
    @PluginMethod public void backgroundCheckStatus(PluginCall call) {
        call.resolve(new JSObject().put("enabled", BackgroundCheckScheduler.enabled(getContext())));
    }
    @PluginMethod public void setBackgroundCheckEnabled(PluginCall call) {
        Boolean enabled = call.getBoolean("enabled");
        if (enabled == null) { call.reject("Missing enabled", "INVALID_ARGUMENT"); return; }
        BackgroundCheckScheduler.setEnabled(getContext(), enabled);
        call.resolve(new JSObject().put("enabled", enabled));
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
