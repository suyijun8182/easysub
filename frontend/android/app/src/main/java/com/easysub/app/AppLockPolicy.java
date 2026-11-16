package com.easysub.app;
import androidx.biometric.BiometricPrompt;
final class AppLockPolicy {
    static boolean validMinutes(int value) { return value == 0 || value == 1 || value == 5 || value == 15; }
    static String errorCode(int code) {
        switch (code) {
            case BiometricPrompt.ERROR_CANCELED:
            case BiometricPrompt.ERROR_USER_CANCELED:
            case BiometricPrompt.ERROR_NEGATIVE_BUTTON: return "CANCELED";
            case BiometricPrompt.ERROR_LOCKOUT:
            case BiometricPrompt.ERROR_LOCKOUT_PERMANENT: return "LOCKOUT";
            default: return "UNAVAILABLE";
        }
    }
}
