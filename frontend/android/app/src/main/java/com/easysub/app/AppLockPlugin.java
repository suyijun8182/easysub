package com.easysub.app;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.view.WindowManager;
import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "AppLock")
public class AppLockPlugin extends Plugin {
    private static final int AUTHENTICATORS = BiometricManager.Authenticators.BIOMETRIC_WEAK | BiometricManager.Authenticators.DEVICE_CREDENTIAL;
    private BiometricPrompt prompt;
    private PluginCall pending;

    private static SharedPreferences preferences(Context context) { return context.getSharedPreferences("easysub-app-lock-v1", Context.MODE_PRIVATE); }
    static JSObject statusFor(Context context) {
        SharedPreferences prefs = preferences(context);
        KeyguardManager keyguard = context.getSystemService(KeyguardManager.class);
        boolean secure = keyguard != null && keyguard.isDeviceSecure();
        boolean available = secure && BiometricManager.from(context).canAuthenticate(AUTHENTICATORS) == BiometricManager.BIOMETRIC_SUCCESS;
        int minutes = prefs.getInt("relockMinutes", 1);
        return new JSObject().put("enabled", prefs.getBoolean("enabled", false)).put("available", available)
            .put("reason", available ? "" : secure ? "UNAVAILABLE" : "NO_DEVICE_CREDENTIAL")
            .put("relockMinutes", AppLockPolicy.validMinutes(minutes) ? minutes : 1);
    }
    static void applyWindowPolicy(Activity activity) {
        if (preferences(activity).getBoolean("enabled", false)) activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        else activity.getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
    @PluginMethod public void status(PluginCall call) { call.resolve(statusFor(getContext())); }

    private void authenticate(PluginCall call, Runnable success) {
        getActivity().runOnUiThread(() -> {
            if (pending != null) { call.reject("Authentication already running", "UNAVAILABLE"); return; }
            if (!Boolean.TRUE.equals(statusFor(getContext()).getBool("available"))) { call.reject("Device authentication unavailable", "UNAVAILABLE"); return; }
            String reason = call.getString("reason", "EasySub");
            if (reason == null || reason.trim().isEmpty() || reason.length() > 160) { call.reject("Invalid reason", "UNAVAILABLE"); return; }
            pending = call;
            prompt = new BiometricPrompt((FragmentActivity) getActivity(), ContextCompat.getMainExecutor(getContext()), new BiometricPrompt.AuthenticationCallback() {
                @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                    if (pending != call) return;
                    pending = null; prompt = null; success.run();
                }
                @Override public void onAuthenticationError(int code, CharSequence message) {
                    if (pending != call) return;
                    pending = null; prompt = null; call.reject("Device authentication ended", AppLockPolicy.errorCode(code));
                }
            });
            try { prompt.authenticate(new BiometricPrompt.PromptInfo.Builder().setTitle("EasySub").setSubtitle(reason).setAllowedAuthenticators(AUTHENTICATORS).build()); }
            catch (Exception error) { pending = null; prompt = null; call.reject("Device authentication unavailable", "UNAVAILABLE"); }
        });
    }
    @PluginMethod public void authenticate(PluginCall call) { authenticate(call, call::resolve); }
    @PluginMethod public void setEnabled(PluginCall call) {
        Boolean enabled = call.getBoolean("enabled");
        Integer minutes = call.getInt("relockMinutes", 1);
        if (enabled == null || minutes == null || !AppLockPolicy.validMinutes(minutes)) { call.reject("Invalid app lock settings", "INVALID_ARGUMENT"); return; }
        authenticate(call, () -> {
            if (!preferences(getContext()).edit().putBoolean("enabled", enabled).putInt("relockMinutes", minutes).commit()) {
                call.reject("Cannot save app lock settings", "UNAVAILABLE"); return;
            }
            applyWindowPolicy(getActivity()); call.resolve(statusFor(getContext()));
        });
    }
    @Override protected void handleOnDestroy() { if (prompt != null) prompt.cancelAuthentication(); }
}
