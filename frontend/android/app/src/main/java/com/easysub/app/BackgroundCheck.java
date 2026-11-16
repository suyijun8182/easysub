package com.easysub.app;

import java.io.IOException;
import java.net.URI;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Decides whether the sync server has changes this device has not pulled yet.
 * It never downloads or merges records: the JS sync engine does that when the app opens.
 * See docs/android-native-background-check.md.
 */
final class BackgroundCheck {
    enum Outcome { NO_CHANGE, NOTIFIED, RETRY, STOPPED }

    static final class Response {
        final int status; final String body;
        Response(int status, String body) { this.status = status; this.body = body == null ? "" : body; }
    }
    interface Http {
        /** Must not follow redirects. */
        Response get(String url, String bearer) throws IOException;
        Response postJson(String url, String json) throws IOException;
    }
    interface Store {
        Snapshot load() throws Exception;
        void updateTokens(String access, String refresh) throws Exception;
        void markNotified(String epoch, long cursor) throws Exception;
        void clear();
    }
    interface Notifier {
        boolean enabled();
        void showChanges(String locale);
    }

    static final class Snapshot {
        String server, accessToken, refreshToken, epoch, locale, notifiedEpoch;
        long cursor, notifiedCursor = -1;

        String toJson() throws JSONException {
            JSONObject json = new JSONObject().put("server", server).put("access_token", accessToken).put("refresh_token", refreshToken)
                .put("epoch", epoch).put("cursor", cursor).put("locale", locale).put("notified_cursor", notifiedCursor);
            if (notifiedEpoch != null) json.put("notified_epoch", notifiedEpoch);
            return json.toString();
        }
        static Snapshot fromJson(String text) throws JSONException {
            JSONObject json = new JSONObject(text);
            Snapshot s = new Snapshot();
            s.server = json.getString("server"); s.accessToken = json.optString("access_token", ""); s.refreshToken = json.optString("refresh_token", "");
            s.epoch = json.getString("epoch"); s.cursor = json.getLong("cursor"); s.locale = json.optString("locale", "zh");
            s.notifiedEpoch = json.has("notified_epoch") ? json.getString("notified_epoch") : null; s.notifiedCursor = json.optLong("notified_cursor", -1);
            return s;
        }
        /** A fresh snapshot from JS must not re-announce a change that was already notified. */
        void keepNotificationMarkerFrom(Snapshot previous) {
            if (previous == null) return;
            notifiedEpoch = previous.notifiedEpoch; notifiedCursor = previous.notifiedCursor;
        }
    }

    /** Same rules as serverUrl() in src/sync/transport.js. */
    static boolean safeServer(String value) {
        try {
            URI uri = new URI(value);
            if (uri.getHost() == null || uri.getRawUserInfo() != null || uri.getRawQuery() != null || uri.getRawFragment() != null) return false;
            if ("https".equals(uri.getScheme())) return true;
            String host = uri.getHost();
            return "http".equals(uri.getScheme()) && ("localhost".equals(host) || "127.0.0.1".equals(host) || "[::1]".equals(host) || "::1".equals(host));
        } catch (Exception error) { return false; }
    }

    private final Http http; private final Store store; private final Notifier notifier;
    BackgroundCheck(Http http, Store store, Notifier notifier) { this.http = http; this.store = store; this.notifier = notifier; }

    Outcome run() {
        Snapshot s;
        try { s = store.load(); } catch (Exception error) { return stop(); }
        if (s == null || !safeServer(s.server)) return stop();
        try {
            Response caps = http.get(s.server + "/api/sync/v1/capabilities", s.accessToken);
            if (caps.status == 401) {
                if (s.refreshToken == null || s.refreshToken.isEmpty()) return stop();
                Response refreshed = http.postJson(s.server + "/api/auth/refresh", new JSONObject().put("refresh_token", s.refreshToken).toString());
                if (refreshed.status == 401 || refreshed.status == 403) return stop();
                if (refreshed.status != 200) return Outcome.RETRY;
                JSONObject tokens = new JSONObject(refreshed.body);
                // The server does not revoke refresh tokens on use, so the app keeps its own pair valid.
                s.accessToken = tokens.getString("access_token"); s.refreshToken = tokens.optString("refresh_token", s.refreshToken);
                store.updateTokens(s.accessToken, s.refreshToken);
                caps = http.get(s.server + "/api/sync/v1/capabilities", s.accessToken);
                if (caps.status == 401) return stop();
            }
            if (caps.status == 403) return stop();
            if (caps.status != 200) return Outcome.RETRY;
            JSONObject body = new JSONObject(caps.body);
            if (body.optInt("protocol") != 1) return stop();
            String epoch = body.getString("epoch"); long cursor = body.getLong("cursor");
            boolean changed = !epoch.equals(s.epoch) || cursor > s.cursor;
            boolean announced = epoch.equals(s.notifiedEpoch) && cursor <= s.notifiedCursor;
            if (!changed || announced || !notifier.enabled()) return Outcome.NO_CHANGE;
            notifier.showChanges(s.locale);
            store.markNotified(epoch, cursor);
            return Outcome.NOTIFIED;
        } catch (Exception error) {
            // Network failures, timeouts, redirects and malformed replies all back off and retry.
            return Outcome.RETRY;
        }
    }

    private Outcome stop() { store.clear(); return Outcome.STOPPED; }
}
