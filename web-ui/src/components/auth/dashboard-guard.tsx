'use client';

import React, { useEffect } from 'react';
import { useFirebaseAuth } from '../providers/firebase-auth-provider';
import { usePathname, useRouter } from 'next/navigation';

export default function DashboardGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useFirebaseAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      const returnTo = pathname || '/dashboard';
      router.replace(`/login?returnTo=${encodeURIComponent(returnTo)}`);
    }
  }, [user, loading, router, pathname]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[200px] text-slate-500 dark:text-slate-400">
        Loading authentication...
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
}
