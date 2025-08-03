import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Star, MessageCircle } from 'lucide-react';

const favoritePhilosophers = [
  {
    name: 'Socrates',
    period: '470-399 BCE',
    conversations: 12,
    rating: 5,
    lastChat: '2 hours ago',
  },
  {
    name: 'Nietzsche',
    period: '1844-1900',
    conversations: 8,
    rating: 5,
    lastChat: '1 day ago',
  },
  {
    name: 'Aristotle',
    period: '384-322 BCE',
    conversations: 15,
    rating: 4,
    lastChat: '3 days ago',
  },
];

export function FavoritePhilosophers() {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Favorite Philosophers</h3>
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/philosophers">Explore More</Link>
          </Button>
        </div>
      </div>
      <div className="px-6 pb-6">
        <div className="space-y-4">
          {favoritePhilosophers.map((philosopher) => (
            <div
              key={philosopher.name}
              className="flex items-center justify-between p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <span className="text-white font-semibold">
                    {philosopher.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <h4 className="font-medium">{philosopher.name}</h4>
                  <p className="text-sm text-muted-foreground">{philosopher.period}</p>
                  <div className="flex items-center space-x-1 mt-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star
                        key={i}
                        className={`w-3 h-3 ${
                          i < philosopher.rating
                            ? 'text-yellow-400 fill-current'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right text-sm">
                  <div className="flex items-center space-x-1 text-muted-foreground">
                    <MessageCircle className="w-4 h-4" />
                    <span>{philosopher.conversations} chats</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Last: {philosopher.lastChat}
                  </p>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/dashboard/chat?philosopher=${philosopher.name}`}>
                    Chat
                  </Link>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
