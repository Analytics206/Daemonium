import React from 'react';
import { MessageCircle, Users, Clock, TrendingUp } from 'lucide-react';

const stats = [
  {
    name: 'Total Conversations',
    value: '12',
    icon: MessageCircle,
    change: '+2.5%',
    changeType: 'positive' as const,
  },
  {
    name: 'Philosophers Explored',
    value: '8',
    icon: Users,
    change: '+1',
    changeType: 'positive' as const,
  },
  {
    name: 'Hours of Dialogue',
    value: '24.3',
    icon: Clock,
    change: '+4.2h',
    changeType: 'positive' as const,
  },
  {
    name: 'Insights Gained',
    value: '47',
    icon: TrendingUp,
    change: '+12',
    changeType: 'positive' as const,
  },
];

export function DashboardStats() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.name}
            className="rounded-lg border bg-card text-card-foreground shadow-sm p-6"
          >
            <div className="flex items-center justify-between space-y-0 pb-2">
              <h3 className="tracking-tight text-sm font-medium">{stat.name}</h3>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                <span className={stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'}>
                  {stat.change}
                </span>{' '}
                from last month
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
