import type { CapacitorConfig } from '@capacitor/cli'

// The iPhone/iPad app: the built web app (dist/) inside a native shell. Build it with `npm run ios`.
const config: CapacitorConfig = {
  appId: 'com.pictalog.app',
  appName: 'Pictalog',
  webDir: 'dist',
  // Black behind the web view, matching the launch screen and the intro, so nothing white shows while it loads.
  backgroundColor: '#000000',
  ios: {
    // The pages pad themselves for the notch and home bar (pt-safe / pb-safe), so the web view fills the screen.
    contentInset: 'never',
  },
}

export default config
