import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { MessageCircle, Clock } from 'lucide-react';

const recentConversations = [
  {
    id: '1',
    philosopher: 'Socrates',
    lastMessage: 'The unexamined life is not worth living...',
    timestamp: '2 hours ago',
    messageCount: 12,
  },
  {
    id: '2',
    philosopher: 'Nietzsche',
    lastMessage: 'What does not kill me makes me stronger...',
    timestamp: '1 day ago',
    messageCount: 8,
  },
  {
    id: '3',
    philosopher: 'Aristotle',
    lastMessage: 'We are what we repeatedly do...',
    timestamp: '3 days ago',
    messageCount: 15,
  },
];

export function RecentConversations() {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Recent Conversations</h3>
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/chat">View All</Link>
          </Button>
        </div>
      </div>
      <div className="px-6 pb-6">
        <div className="space-y-4">
          {recentConversations.map((conversation) => (
            <div
              key={conversation.id}
              className="flex items-center justify-between p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <span className="text-white font-semibold text-sm">
                    {conversation.philosopher.charAt(0)}
                  </span>
                </div>
                <div>
                  <h4 className="font-medium">{conversation.philosopher}</h4>
                  <p className="text-sm text-muted-foreground truncate max-w-xs">
                    {conversation.lastMessage}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <MessageCircle className="w-4 h-4" />
                  <span>{conversation.messageCount}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4" />
                  <span>{conversation.timestamp}</span>
                </div>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/dashboard/chat/${conversation.id}`}>Continue</Link>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
