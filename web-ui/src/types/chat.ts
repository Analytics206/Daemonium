export interface Message {
  id: string;
  role: 'user' | 'philosopher';
  content: string;
  timestamp: Date;
  metadata?: {
    tokens?: number;
    processingTime?: number;
    emotion?: string;
    confidence?: number;
  };
}

export interface Conversation {
  _id: string;
  userId: string;
  philosopherId: string;
  philosopher?: {
    id: string;
    name: string;
    avatar: string;
    era: string;
  };
  title: string;
  messages: Message[];
  context?: {
    summary: string;
    keyTopics: string[];
    userInsights: string[];
    philosopherPersonality: {
      adaptedTone: string;
      userRelationship: string;
    };
  };
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  philosopherName: string;
  philosopherAvatar: string;
  lastMessage: string;
  lastMessageTime: Date;
  messageCount: number;
  isActive: boolean;
}

export interface ChatState {
  currentConversation: Conversation | null;
  conversations: ConversationSummary[];
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;
}

export interface SendMessageRequest {
  conversationId?: string;
  philosopherId: string;
  message: string;
}

export interface SendMessageResponse {
  conversationId: string;
  message: Message;
}
