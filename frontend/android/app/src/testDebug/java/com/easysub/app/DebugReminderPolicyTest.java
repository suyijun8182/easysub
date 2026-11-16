package com.easysub.app;
import static org.junit.Assert.*;
import org.junit.Test;
public class DebugReminderPolicyTest {
    @Test public void acceptsOnlyIsolatedTestNamesAndBoundedDelays() {
        assertTrue(DebugReminderPolicy.allowed("DEVICE_TEST_NOTIFY · 1.00 USD", 60));
        assertFalse(DebugReminderPolicy.allowed("Netflix", 60));
        assertFalse(DebugReminderPolicy.allowed(null, 60));
        assertFalse(DebugReminderPolicy.allowed("DEVICE_TEST_NOTIFY", 1));
        assertFalse(DebugReminderPolicy.allowed("DEVICE_TEST_NOTIFY", 601));
    }
}
