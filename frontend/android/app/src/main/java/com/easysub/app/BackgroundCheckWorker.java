package com.easysub.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Periodic job: asks the sync server whether it has changes and posts one local notification. */
public class BackgroundCheckWorker extends Worker {
    static final String CHANNEL = "easysub-sync-v1";
    private static final String TAG = "easysub-sync";
    private static final int ID = 1;

    /** The app just synced, so a pending "new changes" notification is stale. */
    static void dismiss(Context context) { NotificationManagerCompat.from(context).cancel(TAG, ID); }
    private static final int MAX_BODY = 64 * 1024;

    public BackgroundCheckWorker(@NonNull Context context, @NonNull WorkerParameters params) { super(context, params); }

    @NonNull @Override public Result doWork() {
        Context context = getApplicationContext();
        if (!BackgroundCheckScheduler.enabled(context)) return Result.success();
        BackgroundCheck.Outcome outcome = new BackgroundCheck(new UrlHttp(), new BackgroundCheckStore(context), new SystemNotifier(context)).run();
        return outcome == BackgroundCheck.Outcome.RETRY ? Result.retry() : Result.success();
    }

    static final class UrlHttp implements BackgroundCheck.Http {
        @Override public BackgroundCheck.Response get(String url, String bearer) throws IOException {
            HttpURLConnection connection = open(url);
            connection.setRequestProperty("Authorization", "Bearer " + bearer);
            return read(connection);
        }
        @Override public BackgroundCheck.Response postJson(String url, String json) throws IOException {
            HttpURLConnection connection = open(url);
            connection.setRequestMethod("POST"); connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json");
            try (OutputStream out = connection.getOutputStream()) { out.write(json.getBytes(StandardCharsets.UTF_8)); }
            return read(connection);
        }
        private static HttpURLConnection open(String url) throws IOException {
            HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(20000); connection.setReadTimeout(20000);
            connection.setUseCaches(false);
            connection.setRequestProperty("Accept", "application/json");
            return connection;
        }
        private static BackgroundCheck.Response read(HttpURLConnection connection) throws IOException {
            try {
                int status = connection.getResponseCode();
                InputStream in = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
                if (in == null) return new BackgroundCheck.Response(status, "");
                try (InputStream body = in; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                    byte[] buffer = new byte[4096]; int n;
                    while ((n = body.read(buffer)) != -1) {
                        if (out.size() + n > MAX_BODY) throw new IOException("Response too large");
                        out.write(buffer, 0, n);
                    }
                    return new BackgroundCheck.Response(status, out.toString("UTF-8"));
                }
            } finally { connection.disconnect(); }
        }
    }

    static final class SystemNotifier implements BackgroundCheck.Notifier {
        private final Context context;
        SystemNotifier(Context context) { this.context = context; }

        static String[] copy(String locale) {
            if ("en".equals(locale)) return new String[]{"Sync", "The web app has new changes. Open EasySub to sync."};
            if ("ru".equals(locale)) return new String[]{"Синхронизация", "В веб-версии есть новые изменения. Откройте EasySub для синхронизации."};
            return new String[]{"同步", "网页端有新的变更，打开 EasySub 同步。"};
        }
        @Override public boolean enabled() {
            NotificationManagerCompat manager = NotificationManagerCompat.from(context);
            if (!manager.areNotificationsEnabled()) return false;
            if (Build.VERSION.SDK_INT >= 26) {
                NotificationChannel channel = context.getSystemService(NotificationManager.class).getNotificationChannel(CHANNEL);
                return channel == null || channel.getImportance() != NotificationManager.IMPORTANCE_NONE;
            }
            return true;
        }
        @Override public void showChanges(String locale) {
            String[] text = copy(locale);
            if (Build.VERSION.SDK_INT >= 26) {
                NotificationChannel channel = new NotificationChannel(CHANNEL, text[0], NotificationManager.IMPORTANCE_DEFAULT);
                channel.setLockscreenVisibility(NotificationCompat.VISIBILITY_PRIVATE);
                context.getSystemService(NotificationManager.class).createNotificationChannel(channel);
            }
            Intent launch = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
            if (launch == null) return;
            launch.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
            PendingIntent open = PendingIntent.getActivity(context, ID, launch, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
            NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL)
                .setSmallIcon(R.drawable.ic_stat_easysub).setContentTitle("EasySub").setContentText(text[1])
                .setStyle(new NotificationCompat.BigTextStyle().bigText(text[1]))
                .setContentIntent(open).setAutoCancel(true).setOnlyAlertOnce(true)
                .setVisibility(NotificationCompat.VISIBILITY_PRIVATE).setCategory(NotificationCompat.CATEGORY_STATUS);
            try { NotificationManagerCompat.from(context).notify(TAG, ID, builder.build()); }
            catch (SecurityException missingPermission) { /* Permission revoked between check and post. */ }
        }
    }
}
