export interface Philosopher {
  _id: string;
  name: string;
  era: 'ancient' | 'medieval' | 'modern' | 'contemporary';
  school: string;
  lifespan: string;
  nationality: string;
  avatar: string;
  description: string;
  keyIdeas: string[];
  famousQuotes: string[];
  personality: {
    tone: string;
    style: string;
    approach: string;
  };
  discussionHooks: string[];
  isPremium: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface PhilosopherCard {
  id: string;
  name: string;
  era: Philosopher['era'];
  school: string;
  avatar: string;
  description: string;
  isPremium: boolean;
}

export interface PhilosopherFilter {
  era?: Philosopher['era'];
  school?: string;
  isPremium?: boolean;
  search?: string;
}

export interface PhilosopherStats {
  totalConversations: number;
  averageRating: number;
  lastConversation?: Date;
  favoriteTopics: string[];
}
