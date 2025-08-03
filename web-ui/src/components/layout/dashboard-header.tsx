'use client';

import React from 'react';
import { Button } from '../ui/button';
import { ThemeToggle } from '../ui/theme-toggle';
import { User, LogOut } from 'lucide-react';
import { signOut, useSession } from 'next-auth/react';

export function DashboardHeader() {
  const { data: session } = useSession();

  const handleSignOut = () => {
    signOut({ callbackUrl: '/' });
  };

  return (
    <header className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Daemonium Dashboard
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <User className="w-4 h-4 text-slate-600 dark:text-slate-400" />
            <span className="text-sm text-slate-700 dark:text-slate-300">
              {session?.user?.name || session?.user?.email || 'User'}
            </span>
          </div>
          
          <ThemeToggle />
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleSignOut}
            className="flex items-center space-x-2"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
