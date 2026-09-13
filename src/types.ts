export type ApplicationType = 'looking_for_team' | 'looking_for_member';
export type ApplicationStatus = 'new' | 'accepted' | 'rejected' | 'cancelled';

export interface TelegramUser {
  id: number;
  username?: string;
  first_name: string;
  is_blocked: boolean;
}

export interface ApplicationRecord {
  id: number;
  user_id: number;
  type: ApplicationType;
  name: string;
  role: string;
  skills: string;
  experience: string;
  looking_for: string;
  project_description?: string;
  availability: string;
  about?: string;
  telegram_contact?: string;
  status: ApplicationStatus;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot' | 'admin';
  text: string;
  timestamp: string;
  inlineKeyboard?: Array<Array<{ text: string; callback_data: string }>>;
  replyKeyboard?: Array<Array<{ text: string }>>;
  appId?: number;
}
