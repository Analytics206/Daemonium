// Client-side Firebase initialization for Web-UI
// Reads from NEXT_PUBLIC_ env vars (see web-ui/.env.example)
import type { FirebaseApp } from 'firebase/app';
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

// Only initialize in the browser to avoid build-time SSR/SSG errors
const isBrowser = typeof window !== 'undefined';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

// Minimal set of required config values to attempt initialization
const hasConfig = Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY)
  && Boolean(process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN)
  && Boolean(process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID)
  && Boolean(process.env.NEXT_PUBLIC_FIREBASE_APP_ID);

let app: FirebaseApp | undefined = undefined;
let auth: ReturnType<typeof getAuth> | undefined = undefined;
let googleProvider: GoogleAuthProvider | undefined = undefined;

if (isBrowser && hasConfig) {
  try {
    app = getApps().length ? getApp() : initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
    // Prompt account selection each time for clarity
    googleProvider.setCustomParameters({ prompt: 'select_account' });
  } catch (err) {
    // Silently degrade if Firebase cannot initialize (e.g., invalid config)
    if (process.env.NODE_ENV !== 'production') {
      // eslint-disable-next-line no-console
      console.warn('Firebase initialization skipped due to error:', err);
    }
  }
} else if (isBrowser && !hasConfig) {
  // In development, log a helpful warning; keep exports undefined to avoid crashes
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.warn('Firebase auth not configured. Set NEXT_PUBLIC_FIREBASE_* env vars to enable login.');
  }
}

export { app, auth, googleProvider };

