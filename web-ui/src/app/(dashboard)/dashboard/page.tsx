import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Your philosophical journey overview and recent conversations.',
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-slate-600 dark:text-slate-400">
          Welcome back to your philosophical journey
        </p>
      </div>
      
      <div className="grid gap-6">
        <div className="rounded-lg border bg-white dark:bg-slate-800 p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">12</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Conversations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">8</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Philosophers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">24.3</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Hours</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">47</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Insights</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
