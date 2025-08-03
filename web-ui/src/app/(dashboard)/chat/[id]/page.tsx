import { Metadata } from 'next';
import ChatInterface from '@/components/chat/chat-interface';

interface ChatPageProps {
  params: Promise<{
    id: string;
  }>;
}

export async function generateMetadata({ params }: ChatPageProps): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Chat Session ${id}`,
    description: 'Continue your philosophical conversation.',
  };
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { id } = await params;
  
  return (
    <div className="flex h-full flex-col">
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
          Chat Session {id}
        </h1>
      </div>
      <div className="flex-1 overflow-hidden">
        <ChatInterface chatId={id} />
      </div>
    </div>
  );
}
