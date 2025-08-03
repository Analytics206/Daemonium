import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { MessageCircle, Star } from 'lucide-react';

const philosophers = [
  {
    name: 'Socrates',
    period: '470-399 BCE',
    description: 'The father of Western philosophy, known for the Socratic method of questioning.',
    specialty: 'Ethics, Epistemology',
    rating: 4.9,
    conversations: 1250,
  },
  {
    name: 'Aristotle',
    period: '384-322 BCE',
    description: 'Student of Plato, founded the Lyceum and made contributions to logic, biology, and ethics.',
    specialty: 'Logic, Biology, Ethics',
    rating: 4.8,
    conversations: 980,
  },
  {
    name: 'Immanuel Kant',
    period: '1724-1804',
    description: 'German philosopher who argued for the existence of synthetic a priori knowledge.',
    specialty: 'Metaphysics, Ethics',
    rating: 4.7,
    conversations: 756,
  },
  {
    name: 'Friedrich Nietzsche',
    period: '1844-1900',
    description: 'German philosopher known for his critique of traditional morality and religion.',
    specialty: 'Existentialism, Ethics',
    rating: 4.6,
    conversations: 892,
  },
  {
    name: 'Plato',
    period: '428-348 BCE',
    description: 'Student of Socrates, founded the Academy in Athens, wrote philosophical dialogues.',
    specialty: 'Political Philosophy, Metaphysics',
    rating: 4.8,
    conversations: 1100,
  },
  {
    name: 'Marcus Aurelius',
    period: '121-180 CE',
    description: 'Roman Emperor and Stoic philosopher, author of Meditations.',
    specialty: 'Stoicism, Ethics',
    rating: 4.5,
    conversations: 634,
  },
];

export function PhilosopherGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {philosophers.map((philosopher) => (
        <div
          key={philosopher.name}
          className="rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="p-6">
            <div className="flex items-center space-x-4 mb-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <span className="text-white font-bold text-xl">
                  {philosopher.name.charAt(0)}
                </span>
              </div>
              <div>
                <h3 className="text-xl font-semibold">{philosopher.name}</h3>
                <p className="text-sm text-muted-foreground">{philosopher.period}</p>
              </div>
            </div>

            <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
              {philosopher.description}
            </p>

            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Specialty:</span>
                <span className="font-medium">{philosopher.specialty}</span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Rating:</span>
                <div className="flex items-center space-x-1">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span className="font-medium">{philosopher.rating}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Conversations:</span>
                <div className="flex items-center space-x-1">
                  <MessageCircle className="w-4 h-4 text-blue-500" />
                  <span className="font-medium">{philosopher.conversations.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <Button className="w-full" asChild>
              <Link href={`/dashboard/chat?philosopher=${encodeURIComponent(philosopher.name)}`}>
                Start Conversation
              </Link>
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
