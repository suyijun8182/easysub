package com.easysub.app;
import static org.junit.Assert.*;
import org.junit.Test;
public class AppLockPolicyTest {
    @Test public void onlySupportedRelockIntervalsAreAccepted() {
        for (int value : new int[]{0,1,5,15}) assertTrue(AppLockPolicy.validMinutes(value));
        for (int value : new int[]{-1,2,60}) assertFalse(AppLockPolicy.validMinutes(value));
    }
    @Test public void terminalAuthenticationErrorsHaveStableCodes() {
        for (int code : new int[]{5,10,13}) assertEquals("CANCELED", AppLockPolicy.errorCode(code));
        for (int code : new int[]{7,9}) assertEquals("LOCKOUT", AppLockPolicy.errorCode(code));
        for (int code : new int[]{1,2,12,14}) assertEquals("UNAVAILABLE", AppLockPolicy.errorCode(code));
    }
}
