#!/usr/bin/env node
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs';
import path from 'path';
import AndroidFCM from '@liamcottle/push-receiver/src/android/fcm.js';

/**
 * Custom FCM+Expo setup that reuses an existing Rust+ AuthToken.
 * Usage: node scripts/fcm_setup_custom.js --auth-token <RustPlusAuthToken> [--config rustplus.config.json]
 */

function getArg(name, defVal = undefined) {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && idx + 1 < process.argv.length) return process.argv[idx + 1];
  return defVal;
}

const authToken = getArg('--auth-token');
const configFile = getArg('--config', 'rustplus.config.json');

if (!authToken) {
  console.error('[!] Missing --auth-token');
  process.exit(1);
}

(async () => {
  try {
    console.log('[*] Registering with FCM (Android) …');
    const apiKey = 'AIzaSyB5y2y-Tzqb4-I4Qnlsh_9naYv_TD8pCvY';
    const projectId = 'rust-companion-app';
    const gcmSenderId = '976529667804';
    const gmsAppId = '1:976529667804:android:d6f1ddeb4403b338fea619';
    const androidPackageName = 'com.facepunch.rust.companion';
    const androidPackageCert = 'E28D05345FB78A7A1A63D70F4A302DBF426CA5AD';

    const fcmCredentials = await AndroidFCM.register(
      apiKey,
      projectId,
      gcmSenderId,
      gmsAppId,
      androidPackageName,
      androidPackageCert
    );

    console.log('[*] Fetching Expo Push Token …');
    const deviceId = uuidv4();
    const response = await axios.post(
      'https://exp.host/--/api/v2/push/getExpoPushToken',
      {
        type: 'fcm',
        deviceId,
        development: false,
        appId: 'com.facepunch.rust.companion',
        deviceToken: fcmCredentials.fcm.token,
        projectId: '49451aca-a822-41e6-ad59-955718d0ff9c'
      },
      { headers: { 'Content-Type': 'application/json' } }
    );
    const expoPushToken = response.data?.data?.expoPushToken;
    if (!expoPushToken) {
      console.error('[!] Failed to fetch Expo Push Token');
      process.exit(1);
    }

    console.log('[*] Registering device with Rust Companion API …');
    await axios.post(
      'https://companion-rust.facepunch.com/api/push/register',
      {
        AuthToken: authToken,
        DeviceId: 'python-rustplus-client',
        PushKind: 3,
        PushToken: expoPushToken
      },
      { headers: { 'Content-Type': 'application/json' } }
    );

    const cfg = {
      fcm_credentials: fcmCredentials,
      expo_push_token: expoPushToken,
      rustplus_auth_token: authToken
    };

    // Write config at project root
    const outPath = path.resolve(process.cwd(), configFile);
    fs.writeFileSync(outPath, JSON.stringify(cfg, null, 2), 'utf8');
    console.log(`[+] Saved ${configFile}`);
    process.exit(0);
  } catch (err) {
    console.error('[!] Error during FCM/Expo setup:', err?.message || err);
    process.exit(1);
  }
})();
