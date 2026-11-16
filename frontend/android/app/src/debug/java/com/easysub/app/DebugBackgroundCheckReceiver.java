package com.easysub.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import androidx.work.Constraints;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;

/**
 * Debug source set only. Runs the same background check once now, so device QA does not wait
 * for the 15-minute period: adb shell am broadcast -n com.easysub.app/.DebugBackgroundCheckReceiver
 */
public class DebugBackgroundCheckReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(BackgroundCheckWorker.class)
            .setConstraints(new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build();
        WorkManager.getInstance(context).enqueueUniqueWork("easysub-background-check-debug", ExistingWorkPolicy.REPLACE, request);
        setResultCode(1);
    }
}
