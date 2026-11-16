package com.easysub.app;

import static org.junit.Assert.*;

import java.io.IOException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import org.junit.Test;

public class BackgroundCheckTest {
    private static final String SERVER = "https://sync.example.com:8443";
    private static final String CAPS = SERVER + "/api/sync/v1/capabilities";
    private static final String REFRESH = SERVER + "/api/auth/refresh";

    private static final class FakeHttp implements BackgroundCheck.Http {
        final Deque<Object> replies = new ArrayDeque<>();
        final List<String> calls = new ArrayList<>();
        FakeHttp reply(int status, String body) { replies.add(new BackgroundCheck.Response(status, body)); return this; }
        FakeHttp fail() { replies.add(new IOException("offline")); return this; }
        private BackgroundCheck.Response next() throws IOException {
            Object reply = replies.remove();
            if (reply instanceof IOException) throw (IOException) reply;
            return (BackgroundCheck.Response) reply;
        }
        @Override public BackgroundCheck.Response get(String url, String bearer) throws IOException { calls.add("GET " + url + " " + bearer); return next(); }
        @Override public BackgroundCheck.Response postJson(String url, String json) throws IOException { calls.add("POST " + url + " " + json); return next(); }
    }

    private static final class FakeStore implements BackgroundCheck.Store {
        BackgroundCheck.Snapshot snapshot;
        boolean cleared;
        FakeStore(BackgroundCheck.Snapshot snapshot) { this.snapshot = snapshot; }
        @Override public BackgroundCheck.Snapshot load() { return snapshot; }
        @Override public void updateTokens(String access, String refresh) { snapshot.accessToken = access; snapshot.refreshToken = refresh; }
        @Override public void markNotified(String epoch, long cursor) { snapshot.notifiedEpoch = epoch; snapshot.notifiedCursor = cursor; }
        @Override public void clear() { cleared = true; snapshot = null; }
    }

    private static final class FakeNotifier implements BackgroundCheck.Notifier {
        boolean allowed = true;
        final List<String> shown = new ArrayList<>();
        @Override public boolean enabled() { return allowed; }
        @Override public void showChanges(String locale) { shown.add(locale); }
    }

    private static BackgroundCheck.Snapshot snapshot(long cursor) {
        BackgroundCheck.Snapshot s = new BackgroundCheck.Snapshot();
        s.server = SERVER; s.accessToken = "access"; s.refreshToken = "refresh"; s.epoch = "epoch-1"; s.cursor = cursor; s.locale = "zh";
        return s;
    }
    private static String caps(String epoch, long cursor) { return "{\"protocol\":1,\"epoch\":\"" + epoch + "\",\"cursor\":" + cursor + "}"; }

    @Test public void unchangedCursorDoesNotNotify() {
        FakeHttp http = new FakeHttp().reply(200, caps("epoch-1", 198));
        FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier();
        assertEquals(BackgroundCheck.Outcome.NO_CHANGE, new BackgroundCheck(http, store, notifier).run());
        assertTrue(notifier.shown.isEmpty());
        assertEquals(List.of("GET " + CAPS + " access"), http.calls);
    }

    @Test public void newServerChangeNotifiesOnceThenAgainOnlyWhenItAdvances() {
        FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier();
        FakeHttp http = new FakeHttp().reply(200, caps("epoch-1", 199)).reply(200, caps("epoch-1", 199)).reply(200, caps("epoch-1", 201));
        BackgroundCheck check = new BackgroundCheck(http, store, notifier);
        assertEquals(BackgroundCheck.Outcome.NOTIFIED, check.run());
        assertEquals(BackgroundCheck.Outcome.NO_CHANGE, check.run());
        assertEquals(BackgroundCheck.Outcome.NOTIFIED, check.run());
        assertEquals(List.of("zh", "zh"), notifier.shown);
        assertEquals(201, store.snapshot.notifiedCursor);
    }

    @Test public void epochChangeCountsAsNewChanges() {
        FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier();
        assertEquals(BackgroundCheck.Outcome.NOTIFIED, new BackgroundCheck(new FakeHttp().reply(200, caps("epoch-2", 3)), store, notifier).run());
        assertEquals("epoch-2", store.snapshot.notifiedEpoch);
    }

    @Test public void expiredAccessTokenIsRefreshedIntoTheSnapshotAndRetriedOnce() {
        FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier();
        FakeHttp http = new FakeHttp().reply(401, "{}").reply(200, "{\"access_token\":\"access-2\",\"refresh_token\":\"refresh-2\"}").reply(200, caps("epoch-1", 198));
        assertEquals(BackgroundCheck.Outcome.NO_CHANGE, new BackgroundCheck(http, store, notifier).run());
        assertEquals(List.of("GET " + CAPS + " access", "POST " + REFRESH + " {\"refresh_token\":\"refresh\"}", "GET " + CAPS + " access-2"), http.calls);
        assertEquals("access-2", store.snapshot.accessToken);
        assertEquals("refresh-2", store.snapshot.refreshToken);
    }

    @Test public void rejectedRefreshClearsSnapshotAndStopsWithoutNotifying() {
        for (int status : new int[]{401, 403}) {
            FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier();
            FakeHttp http = new FakeHttp().reply(401, "{}").reply(status, "{}");
            assertEquals(BackgroundCheck.Outcome.STOPPED, new BackgroundCheck(http, store, notifier).run());
            assertTrue(store.cleared); assertTrue(notifier.shown.isEmpty());
        }
    }

    @Test public void forbiddenAccountStops() {
        FakeStore store = new FakeStore(snapshot(198));
        assertEquals(BackgroundCheck.Outcome.STOPPED, new BackgroundCheck(new FakeHttp().reply(403, "{}"), store, new FakeNotifier()).run());
        assertTrue(store.cleared);
    }

    @Test public void transientFailuresRetryAndKeepTheSnapshot() {
        for (FakeHttp http : new FakeHttp[]{ new FakeHttp().fail(), new FakeHttp().reply(502, "bad gateway"), new FakeHttp().reply(302, ""), new FakeHttp().reply(200, "not json"), new FakeHttp().reply(401, "{}").fail() }) {
            FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier();
            assertEquals(BackgroundCheck.Outcome.RETRY, new BackgroundCheck(http, store, notifier).run());
            assertFalse(store.cleared); assertTrue(notifier.shown.isEmpty());
        }
    }

    @Test public void unsafeServerAddressesAreRejectedBeforeAnyRequest() {
        for (String server : new String[]{"http://sync.example.com", "https://user:pw@sync.example.com", "https://sync.example.com/?x=1", "https://sync.example.com/#a", "ftp://sync.example.com", "not a url"}) {
            BackgroundCheck.Snapshot s = snapshot(198); s.server = server;
            FakeHttp http = new FakeHttp(); FakeStore store = new FakeStore(s);
            assertEquals(server, BackgroundCheck.Outcome.STOPPED, new BackgroundCheck(http, store, new FakeNotifier()).run());
            assertTrue(http.calls.isEmpty()); assertTrue(store.cleared);
        }
        assertTrue(BackgroundCheck.safeServer("http://localhost:8000"));
        assertTrue(BackgroundCheck.safeServer("http://127.0.0.1:8000"));
        assertTrue(BackgroundCheck.safeServer(SERVER));
    }

    @Test public void withoutNotificationPermissionNothingIsMarkedSoALaterGrantStillAlerts() {
        FakeStore store = new FakeStore(snapshot(198)); FakeNotifier notifier = new FakeNotifier(); notifier.allowed = false;
        assertEquals(BackgroundCheck.Outcome.NO_CHANGE, new BackgroundCheck(new FakeHttp().reply(200, caps("epoch-1", 199)), store, notifier).run());
        assertNull(store.snapshot.notifiedEpoch);
        notifier.allowed = true;
        assertEquals(BackgroundCheck.Outcome.NOTIFIED, new BackgroundCheck(new FakeHttp().reply(200, caps("epoch-1", 199)), store, notifier).run());
    }

    @Test public void missingSnapshotStopsQuietly() {
        FakeHttp http = new FakeHttp();
        assertEquals(BackgroundCheck.Outcome.STOPPED, new BackgroundCheck(http, new FakeStore(null), new FakeNotifier()).run());
        assertTrue(http.calls.isEmpty());
    }

    @Test public void snapshotJsonRoundTripsAndKeepsNotificationMarkerAcrossAppUpdates() throws Exception {
        BackgroundCheck.Snapshot s = snapshot(198); s.notifiedEpoch = "epoch-1"; s.notifiedCursor = 199;
        BackgroundCheck.Snapshot copy = BackgroundCheck.Snapshot.fromJson(s.toJson());
        assertEquals(s.toJson(), copy.toJson());
        BackgroundCheck.Snapshot fresh = snapshot(200);
        fresh.keepNotificationMarkerFrom(copy);
        assertEquals(199, fresh.notifiedCursor);
        assertEquals("epoch-1", fresh.notifiedEpoch);
    }

    @Test public void cursorFromJavaScriptAcceptsAnyWholeNonNegativeNumber() {
        // Capacitor delivers small JS numbers as Integer; PluginCall.getLong() would return null for them.
        assertEquals(Long.valueOf(198), BackgroundCheck.cursor(198));
        assertEquals(Long.valueOf(5000000000L), BackgroundCheck.cursor(5000000000L));
        assertEquals(Long.valueOf(7), BackgroundCheck.cursor(7.0));
        for (Object bad : new Object[]{null, -1, 1.5, "198", Double.NaN}) assertNull(String.valueOf(bad), BackgroundCheck.cursor(bad));
    }
}
