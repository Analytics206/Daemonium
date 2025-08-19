'use client';

import * as React from 'react';
import { FirebaseAuthProvider } from './firebase-auth-provider';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return <FirebaseAuthProvider>{children}</FirebaseAuthProvider>;
}
