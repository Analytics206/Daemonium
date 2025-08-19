import { DashboardHeader } from '../../components/layout/dashboard-header';
import { DashboardSidebar } from '../../components/layout/dashboard-sidebar';
import DashboardGuard from '../../components/auth/dashboard-guard';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardGuard>
      <div className="flex min-h-screen">
        <DashboardSidebar />
        <div className="flex-1 flex flex-col">
          <DashboardHeader />
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </DashboardGuard>
  );
}
