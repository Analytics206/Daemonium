'use client';

import * as React from 'react';

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  // Simple placeholder for now - can be enhanced with React Query later
  return <>{children}</>;
}
