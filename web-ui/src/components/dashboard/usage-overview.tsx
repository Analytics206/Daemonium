import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Mon', conversations: 2 },
  { name: 'Tue', conversations: 4 },
  { name: 'Wed', conversations: 1 },
  { name: 'Thu', conversations: 6 },
  { name: 'Fri', conversations: 3 },
  { name: 'Sat', conversations: 5 },
  { name: 'Sun', conversations: 2 },
];

export function UsageOverview() {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6">
        <h3 className="text-lg font-semibold">Weekly Activity</h3>
        <p className="text-sm text-muted-foreground">
          Your philosophical conversations this week
        </p>
      </div>
      <div className="px-6 pb-6">
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="conversations" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
