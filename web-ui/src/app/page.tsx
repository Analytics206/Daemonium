import { Metadata } from 'next';
import HeroSection from '@/components/sections/hero-section';
import FeaturedPhilosophers from '@/components/sections/featured-philosophers';

export const metadata: Metadata = {
  title: 'Daemonium - Converse with Philosophers',
  description: 'Engage in meaningful conversations with AI-powered philosopher personas. Explore wisdom from ancient to contemporary thinkers.',
};

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col">
      <HeroSection />
      <FeaturedPhilosophers />
    </main>
  );
}
