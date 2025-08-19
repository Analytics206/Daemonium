'use client';

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { User } from 'firebase/auth';
import { app, auth, googleProvider } from '../../lib/firebase';
import { onAuthStateChanged, signInWithPopup, signInWithRedirect, signOut, getAuth, GoogleAuthProvider } from 'firebase/auth';

interface FirebaseAuthContextValue {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOutUser: () => Promise<void>;
}

const FirebaseAuthContext = createContext<FirebaseAuthContextValue | undefined>(undefined);

export function FirebaseAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let cleanup: (() => void) | undefined;
    try {
      const localAuth = auth ?? getAuth();
      cleanup = onAuthStateChanged(localAuth, (u: User | null) => {
        setUser(u);
        setLoading(false);
      });
    } catch {
      // Missing Firebase config; remain unauthenticated but don't crash
      setLoading(false);
    }
    return () => {
      if (cleanup) cleanup();
    };
  }, []);

  const signInWithGoogleFn = async () => {
    // Try to reconstruct auth/provider if the module-level exports are undefined
    let localAuth = auth;
    try {
      if (!localAuth) localAuth = getAuth();
    } catch {
      try {
        if (!localAuth && app) localAuth = getAuth(app);
      } catch {
        // ignore; we'll handle missing auth below
      }
    }
    const localProvider = googleProvider ?? new GoogleAuthProvider();

    if (!localAuth) {
      throw new Error('Firebase auth not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    }

    try {
      await signInWithPopup(localAuth, localProvider);
    } catch (err: any) {
      // Fallback to redirect for common environment issues and argument errors
      const code = err?.code as string | undefined;
      if (
        code === 'auth/popup-blocked' ||
        code === 'auth/cancelled-popup-request' ||
        code === 'auth/operation-not-supported-in-this-environment' ||
        code === 'auth/argument-error'
      ) {
        await signInWithRedirect(localAuth, localProvider);
        return;
      }
      throw err;
    }
  };

  const signOutUserFn = async () => {
    try {
      const localAuth = auth ?? getAuth();
      await signOut(localAuth);
    } catch {
      // ignore if auth is not configured
    }
  };

  const value = useMemo(
    () => ({ user, loading, signInWithGoogle: signInWithGoogleFn, signOutUser: signOutUserFn }),
    [user, loading]
  );

  return <FirebaseAuthContext.Provider value={value}>{children}</FirebaseAuthContext.Provider>;
}

export function useFirebaseAuth() {
  const ctx = useContext(FirebaseAuthContext);
  if (!ctx) throw new Error('useFirebaseAuth must be used within FirebaseAuthProvider');
  return ctx;
}

