package com.easysub.app;

import com.getcapacitor.BridgeActivity;
import android.os.Bundle;

public class MainActivity extends BridgeActivity {
    @Override public void onCreate(Bundle savedInstanceState) {
        registerPlugin(EasySubDevicePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
