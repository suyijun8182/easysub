package com.easysub.app;
final class DebugReminderPolicy {
    static boolean allowed(String body, int delaySeconds) {
        return body != null && body.startsWith("DEVICE_TEST_") && delaySeconds >= 30 && delaySeconds <= 600;
    }
}
