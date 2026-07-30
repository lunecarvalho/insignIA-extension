// Minimal types used by the extension code
export type Message = {
  role: 'agent' | 'customer' | string;
  text: string;
  timestamp?: string | number;
};

export type Conversation = {
  id?: string;
  url?: string;
  messages: Message[];
};

export type AnalysisResult = {
  reason: { category: string; subcategory: string; confidence: number };
  sentiment: { score: number; label: 'negative' | 'neutral' | 'positive' };
  quality: { score: number; checklist: Record<string, boolean>; notes?: string };
  trends: Record<string, number>;
  insights: string[];
};
