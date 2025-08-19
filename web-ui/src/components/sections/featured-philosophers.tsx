import React from 'react';
import { Button } from '../ui/button';
import Image from 'next/image';

const featuredPhilosophers = [
  {
    name: 'Socrates',
    period: '470-399 BCE',
    description: 'The father of Western philosophy, known for the Socratic method of questioning.',
    image: '/images/socrates01.png',
  },
  {
    name: 'Plato',
    period: '427-347 BCE',
    description: 'Student of Socrates, founded the Academy and made contributions to logic, biology, and ethics.',
    image: '/images/plato01.png',
  },
  {
    name: 'Immanuel Kant',
    period: '1724-1804',
    description: 'German philosopher who argued for the existence of synthetic a priori knowledge.',
    image: '/images/Immanuel_Kant01.png',
  },
  {
    name: 'Friedrich Nietzsche',
    period: '1844-1900',
    description: 'German philosopher known for his critique of traditional morality and religion.',
    image: '/images/nietzsche01.png',
  },
];

export default function FeaturedPhilosophers() {
  return (
    <section className="py-24 bg-white dark:bg-slate-900">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl">
            Featured Philosophers
          </h2>
          <p className="mt-4 text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Engage in meaningful conversations with history's most influential thinkers
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {featuredPhilosophers.map((philosopher) => (
            <div
              key={philosopher.name}
              className="bg-slate-50 dark:bg-slate-800 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="mb-4">
                {philosopher.image ? (
                  <Image
                    src={philosopher.image}
                    alt={philosopher.name}
                    width={64}
                    height={64}
                    className="w-16 h-16 rounded-full object-cover"
                    priority
                  />
                ) : (
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-xl">
                      {philosopher.name.charAt(0)}
                    </span>
                  </div>
                )}
              </div>
              
              <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                {philosopher.name}
              </h3>
              
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                {philosopher.period}
              </p>
              
              <p className="text-slate-600 dark:text-slate-300 text-sm mb-4 line-clamp-3">
                {philosopher.description}
              </p>
              
              <Button variant="outline" size="sm" className="w-full">
                Start Conversation
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
