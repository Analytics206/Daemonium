import { Metadata } from 'next';
import { PhilosopherGrid } from '../../../components/philosophers/philosopher-grid';
import { PhilosopherFilters } from '../../../components/philosophers/philosopher-filters';
import { PhilosopherSearch } from '../../../components/philosophers/philosopher-search';

export const metadata: Metadata = {
  title: 'Philosophers',
  description: 'Explore and select from our collection of AI-powered philosopher personas.',
};

export default function PhilosophersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Philosophers</h1>
        <p className="text-muted-foreground">
          Choose a philosopher to begin your conversation
        </p>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <PhilosopherSearch />
        <PhilosopherFilters />
      </div>

      <PhilosopherGrid />
    </div>
  );
}
