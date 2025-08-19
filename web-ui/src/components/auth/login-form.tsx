'use client';

import React, { useEffect, useState } from 'react';
import { signInWithEmailAndPassword, getRedirectResult, getAuth } from 'firebase/auth';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useFirebaseAuth } from '../providers/firebase-auth-provider';
import { useRouter, useSearchParams } from 'next/navigation';
import { auth } from '../../lib/firebase';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { signInWithGoogle, user } = useFirebaseAuth();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = searchParams.get('returnTo') || '/chat';

  // If the user is already signed in (e.g., after redirect), send them on
  useEffect(() => {
    if (user) {
      const stored = typeof window !== 'undefined' ? sessionStorage.getItem('auth_return_to') : null;
      const dest = stored || returnTo;
      if (stored) sessionStorage.removeItem('auth_return_to');
      router.replace(dest);
    }
  }, [user, returnTo, router]);

  // Surface any redirect result errors (if signInWithRedirect was used)
  useEffect(() => {
    let mounted = true;
    const checkRedirect = async () => {
      try {
        // Only attempt when Firebase auth is initialized
        const localAuth = auth ?? getAuth();
        await getRedirectResult(localAuth);
        // Success or null result handled by onAuthStateChanged via provider
      } catch (err: any) {
        if (!mounted) return;
        console.error('Firebase redirect result error:', err);
        const code = err?.code as string | undefined;
        if (code === 'auth/unauthorized-domain') {
          setErrorMsg('This domain is not authorized in Firebase Authentication settings. Add localhost to Authorized domains.');
        } else if (code === 'auth/operation-not-allowed') {
          setErrorMsg('Google sign-in is not enabled for this project. Enable it in Firebase Console > Authentication > Sign-in method.');
        } else if (code) {
          setErrorMsg(`Google redirect sign-in failed: ${code}`);
        } else {
          setErrorMsg('Google redirect sign-in failed.');
        }
      }
    };
    // Only attempt in the browser
    if (typeof window !== 'undefined') {
      void checkRedirect();
    }
    return () => {
      mounted = false;
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const localAuth = auth ?? getAuth();
      await signInWithEmailAndPassword(localAuth, email, password);
      router.replace(returnTo);
    } catch (error: any) {
      console.error('Login error:', error);
      const code = error?.code as string | undefined;
      if (code) {
        if (code === 'auth/invalid-credential' || code === 'auth/wrong-password') {
          setErrorMsg('Invalid email or password.');
        } else if (code === 'auth/user-not-found') {
          setErrorMsg('No user found with this email.');
        } else {
          setErrorMsg(`Sign in failed: ${code}`);
        }
      } else {
        setErrorMsg('Sign in failed.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Email
        </label>
        <Input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mt-1"
          placeholder="Enter your email"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Password
        </label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="mt-1"
          placeholder="Enter your password"
        />
      </div>

      {errorMsg && (
        <div className="text-sm text-red-600 dark:text-red-400" role="alert">
          {errorMsg}
        </div>
      )}

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full"
      >
        {isLoading ? 'Signing in...' : 'Sign in'}
      </Button>

      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-slate-200 dark:border-slate-700" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-transparent px-2 text-slate-500 dark:text-slate-400">or</span>
        </div>
      </div>

      <Button
        type="button"
        onClick={async () => {
          try {
            setIsGoogleLoading(true);
            setErrorMsg(null);
            // Persist intended destination across signInWithRedirect flow
            if (typeof window !== 'undefined') {
              sessionStorage.setItem('auth_return_to', returnTo);
            }
            await signInWithGoogle();
            // Do not navigate immediately. If popup flow succeeds, onAuthStateChanged will redirect.
            // If redirect flow is used, the browser will navigate to Google and back, then our effect will handle routing.
          } catch (err: any) {
            console.error('Google sign-in failed:', err);
            const code = err?.code as string | undefined;
            if (code === 'auth/operation-not-allowed') {
              setErrorMsg('Google sign-in is not enabled for this project. Enable it in Firebase Console > Authentication > Sign-in method.');
            } else if (code === 'auth/popup-blocked') {
              setErrorMsg('Popup was blocked. We tried redirect sign-in automatically; if it did not happen, please allow popups and try again.');
            } else if (code === 'auth/popup-closed-by-user') {
              setErrorMsg('Popup closed before completing sign-in.');
            } else if (code === 'auth/unauthorized-domain') {
              setErrorMsg('This domain is not authorized in Firebase Authentication settings. Add localhost to Authorized domains.');
            } else if (code) {
              setErrorMsg(`Google sign-in failed: ${code}`);
            } else {
              setErrorMsg('Google sign-in failed.');
            }
          } finally {
            setIsGoogleLoading(false);
          }
        }}
        disabled={isGoogleLoading}
        className="w-full bg-white text-slate-900 border border-slate-300 hover:bg-slate-50 dark:bg-slate-200 dark:text-slate-900"
      >
        {isGoogleLoading ? 'Connecting…' : 'Continue with Google'}
      </Button>

      <div className="text-center">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-600 hover:text-blue-500 dark:text-blue-400">
            Sign up
          </a>
        </p>
      </div>
    </form>
  );
}

