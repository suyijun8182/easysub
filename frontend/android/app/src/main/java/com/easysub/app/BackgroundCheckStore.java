package com.easysub.app;

import android.content.Context;

/** Encrypted snapshot for the background check, kept apart from the main local database. */
final class BackgroundCheckStore implements BackgroundCheck.Store {
    static final String FILE = "bg-check-v1.enc";
    private final Context context;
    BackgroundCheckStore(Context context) { this.context = context.getApplicationContext(); }

    /** Called by JS after a complete sync. Keeps the "already notified" marker so it is not re-announced. */
    static void save(Context context, BackgroundCheck.Snapshot fresh) throws Exception {
        EncryptedFile.update(context, FILE, current -> {
            if (current != null) {
                try { fresh.keepNotificationMarkerFrom(BackgroundCheck.Snapshot.fromJson(current)); } catch (Exception ignored) { /* Replace a damaged snapshot. */ }
            }
            return fresh.toJson();
        });
    }
    static boolean exists(Context context) {
        try { return EncryptedFile.read(context, FILE) != null; } catch (Exception error) { return false; }
    }
    static void delete(Context context) { EncryptedFile.delete(context, FILE); }

    @Override public BackgroundCheck.Snapshot load() throws Exception {
        String text = EncryptedFile.read(context, FILE);
        return text == null ? null : BackgroundCheck.Snapshot.fromJson(text);
    }
    @Override public void updateTokens(String access, String refresh) throws Exception {
        EncryptedFile.update(context, FILE, current -> {
            if (current == null) return null;
            BackgroundCheck.Snapshot s = BackgroundCheck.Snapshot.fromJson(current);
            s.accessToken = access; s.refreshToken = refresh;
            return s.toJson();
        });
    }
    @Override public void markNotified(String epoch, long cursor) throws Exception {
        EncryptedFile.update(context, FILE, current -> {
            if (current == null) return null;
            BackgroundCheck.Snapshot s = BackgroundCheck.Snapshot.fromJson(current);
            s.notifiedEpoch = epoch; s.notifiedCursor = cursor;
            return s.toJson();
        });
    }
    @Override public void clear() { delete(context); BackgroundCheckScheduler.cancel(context); }
}
