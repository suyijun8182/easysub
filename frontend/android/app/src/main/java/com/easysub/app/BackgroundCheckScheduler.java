package com.easysub.app;

import android.content.Context;
import androidx.work.BackoffPolicy;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import java.util.concurrent.TimeUnit;

/** Owns the user toggle and the single periodic WorkManager job. */
final class BackgroundCheckScheduler {
    static final String WORK = "easysub-background-check";
    private static final String PREFS = "easysub-background-check-v1";
    private BackgroundCheckScheduler() {}

    static boolean enabled(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean("enabled", true);
    }
    static void setEnabled(Context context, boolean enabled) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean("enabled", enabled).apply();
        sync(context);
    }
    /** Schedules the job when enabled and a snapshot exists; cancels it otherwise. */
    static void sync(Context context) {
        if (!enabled(context) || !BackgroundCheckStore.exists(context)) { cancel(context); return; }
        PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(BackgroundCheckWorker.class, 15, TimeUnit.MINUTES)
            .setConstraints(new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 1, TimeUnit.MINUTES)
            .build();
        // KEEP: repeated snapshots from foreground syncs must not reset the 15-minute period.
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(WORK, ExistingPeriodicWorkPolicy.KEEP, request);
    }
    static void cancel(Context context) { WorkManager.getInstance(context).cancelUniqueWork(WORK); }
}
