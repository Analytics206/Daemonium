'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { Home, MessageCircle, Users, Settings } from 'lucide-react';

const sidebarItems = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home,
  },
  {
    name: 'Chat',
    href: '/dashboard/chat',
    icon: MessageCircle,
  },
  {
    name: 'Philosophers',
    href: '/dashboard/philosophers',
    icon: Users,
  },
  {
    name: 'Settings',
    href: '/dashboard/settings',
    icon: Settings,
  },
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700">
      <div className="p-6">
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Daemonium
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Philosophy Dashboard
          </p>
        </div>

        <nav className="space-y-2">
          {sidebarItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
            const Icon = item.icon;

            return (
              <Link key={item.name} href={item.href}>
                <Button
                  variant={isActive ? 'default' : 'ghost'}
                  className={cn(
                    'w-full justify-start',
                    isActive && 'bg-blue-600 text-white hover:bg-blue-700'
                  )}
                >
                  <Icon className="w-4 h-4 mr-3" />
                  {item.name}
                </Button>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
