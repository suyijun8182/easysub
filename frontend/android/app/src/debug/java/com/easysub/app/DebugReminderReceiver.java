package com.easysub.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import com.capacitorjs.plugins.localnotifications.LocalNotification;
import com.capacitorjs.plugins.localnotifications.LocalNotificationManager;
import com.capacitorjs.plugins.localnotifications.NotificationStorage;
import com.getcapacitor.CapConfig;
import com.getcapacitor.JSObject;
import java.text.SimpleDateFormat;
import java.util.Collections;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

/** Debug source set only. Moves an existing isolated test reminder through the plugin's normal storage and alarm paths. */
public class DebugReminderReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        try {
            int delay = intent.getIntExtra("delaySeconds", 60);
            String id = Integer.toString(intent.getIntExtra("notificationId", 0));
            NotificationStorage storage = new NotificationStorage(context);
            JSObject row = storage.getSavedNotificationAsJSObject(id);
            if (row == null || !DebugReminderPolicy.allowed(row.getString("body"), delay)) return;
            JSObject extra = row.getJSObject("extra");
            if (extra == null || !"reminder".equals(extra.getString("easysubKind"))) return;
            SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.ROOT);
            format.setTimeZone(TimeZone.getTimeZone("UTC"));
            row.put("schedule", new JSObject().put("at", format.format(new Date(System.currentTimeMillis() + delay * 1000L))));
            row.put("isExactNotification", false);
            LocalNotification notification = LocalNotification.Companion.buildNotificationFromJSObject(row);
            storage.appendNotifications(Collections.singletonList(notification));
            new LocalNotificationManager(storage, null, context, CapConfig.loadDefault(context)).schedule(null, Collections.singletonList(notification));
            setResultCode(1);
        } catch (Exception error) { setResultCode(0); }
    }
}
