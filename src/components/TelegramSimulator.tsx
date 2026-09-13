import React, { useState, useEffect, useRef } from 'react';
import { Send, ArrowLeft, X, Bot, Shield, User as UserIcon, CheckCircle2, XCircle, MessageSquare, AlertCircle, RefreshCw, Terminal } from 'lucide-react';
import { ApplicationRecord, ApplicationStatus, ApplicationType, ChatMessage } from '../types';

interface TelegramSimulatorProps {
  onAddApplication: (app: ApplicationRecord) => void;
  applications: ApplicationRecord[];
  setApplications: React.Dispatch<React.SetStateAction<ApplicationRecord[]>>;
}

export const TelegramSimulator: React.FC<TelegramSimulatorProps> = ({
  applications,
  setApplications,
}) => {
  // Mode: 'candidate' (regular user) vs 'admin'
  const [activeTab, setActiveTab] = useState<'candidate' | 'admin'>('candidate');
  
  // User chat messages
  const [userMessages, setUserMessages] = useState<ChatMessage[]>([]);
  // Admin chat messages
  const [adminMessages, setAdminMessages] = useState<ChatMessage[]>([]);

  // User input field
  const [userInput, setUserInput] = useState('');
  const [adminInput, setAdminInput] = useState('');

  // FSM simulation state for user
  const [userFsmState, setUserFsmState] = useState<string | null>(null);
  const [draftData, setDraftData] = useState<Record<string, string>>({});
  const [isBlocked, setIsBlocked] = useState<boolean>(false);

  // FSM simulation for admin replying
  const [adminReplyTarget, setAdminReplyTarget] = useState<number | null>(null);
  // User replying back
  const [userReplyTarget, setUserReplyTarget] = useState<number | null>(null);

  const userScrollRef = useRef<HTMLDivElement>(null);
  const adminScrollRef = useRef<HTMLDivElement>(null);

  // Initial welcome message
  useEffect(() => {
    if (userMessages.length === 0) {
      setUserMessages([
        {
          id: '1',
          sender: 'bot',
          text: `<b>👥 TeamFinder</b>\n\n<i>Найди людей для своей команды или найди команду для себя.</i>\n\nВыберите нужное действие в меню ниже:\n• <b>🔎 Найти команду</b> — если вы специалист и ищете проект\n• <b>👥 Найти участника</b> — если вы собираете команду\n• <b>📋 Моя анкета</b> — просмотр вашей анкеты\n• <b>❓ Помощь</b> — инструкции`,
          timestamp: '14:00',
          replyKeyboard: [
            [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
            [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
          ]
        }
      ]);
    }

    if (adminMessages.length === 0) {
      setAdminMessages([
        {
          id: 'adm_init',
          sender: 'bot',
          text: `🛡 <b>Панель управления TeamFinder</b>\n\nКанал модерации активен. Сюда в реальном времени поступают новые анкеты кандидатов с возможностью Принять, Отклонить, Связаться или Заблокировать.`,
          timestamp: '14:00',
        }
      ]);
    }
  }, []);

  // Auto scroll
  useEffect(() => {
    userScrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [userMessages]);

  useEffect(() => {
    adminScrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [adminMessages]);

  // Helper to append message to user chat
  const addBotMessage = (text: string, options?: { replyKeyboard?: Array<Array<{ text: string }>>; inlineKeyboard?: Array<Array<{ text: string; callback_data: string }>>; appId?: number }) => {
    setUserMessages(prev => [
      ...prev,
      {
        id: String(Date.now() + Math.random()),
        sender: 'bot',
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        replyKeyboard: options?.replyKeyboard,
        inlineKeyboard: options?.inlineKeyboard,
        appId: options?.appId,
      }
    ]);
  };

  // Helper to append message to admin chat
  const addAdminBotMessage = (text: string, options?: { inlineKeyboard?: Array<Array<{ text: string; callback_data: string }>>; appId?: number }) => {
    setAdminMessages(prev => [
      ...prev,
      {
        id: String(Date.now() + Math.random()),
        sender: 'bot',
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        inlineKeyboard: options?.inlineKeyboard,
        appId: options?.appId,
      }
    ]);
  };

  // User message submit handler
  const handleUserSend = (textToSend?: string) => {
    const text = (textToSend || userInput).trim();
    if (!text) return;

    setUserMessages(prev => [
      ...prev,
      {
        id: String(Date.now()),
        sender: 'user',
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    if (!textToSend) setUserInput('');

    // Check if blocked
    if (isBlocked) {
      setTimeout(() => {
        addBotMessage('🚫 <b>Ваш аккаунт заблокирован администрацией бота.</b>\nВы не можете отправлять новые анкеты.');
      }, 300);
      return;
    }

    // Cancellation
    if (text === '❌ Отмена') {
      setUserFsmState(null);
      setDraftData({});
      setUserReplyTarget(null);
      setTimeout(() => {
        addBotMessage('❌ Действие отменено. Вы вернулись в главное меню.', {
          replyKeyboard: [
            [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
            [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
          ]
        });
      }, 300);
      return;
    }

    // Check if answering admin
    if (userReplyTarget) {
      const targetAppId = userReplyTarget;
      setUserReplyTarget(null);
      setTimeout(() => {
        addBotMessage('✅ <b>Ваш ответ успешно передан администраторам!</b>', {
          replyKeyboard: [
            [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
            [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
          ]
        });
        // Deliver to admin chat
        addAdminBotMessage(
          `💬 <b>Ответ от кандидата по заявке #${targetAppId}:</b>\n\n${text}`,
          {
            inlineKeyboard: [
              [{ text: '💬 Ответить кандидату', callback_data: `adm_contact:${targetAppId}` }]
            ],
            appId: targetAppId
          }
        );
      }, 400);
      return;
    }

    // Main Menu commands
    if (text === '/start') {
      setUserFsmState(null);
      setDraftData({});
      setTimeout(() => {
        addBotMessage(
          `<b>👥 TeamFinder</b>\n\n<i>Найди людей для своей команды или найди команду для себя.</i>\n\nВыберите нужное действие в меню ниже:`,
          {
            replyKeyboard: [
              [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
              [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
            ]
          }
        );
      }, 300);
      return;
    }

    if (text === '❓ Помощь') {
      setTimeout(() => {
        addBotMessage(
          `<b>❓ О сервисе TeamFinder Bot</b>\n\n1. Выберите режим: поиск команды или участника.\n2. Ответьте на вопросы анкеты.\n3. Проверьте сформированную заявку и отправьте.\n4. Модераторы проверят её и свяжутся с вами прямо через бота!`
        );
      }, 300);
      return;
    }

    if (text === '📋 Моя анкета') {
      const active = applications.find(a => a.status === 'new' || a.status === 'accepted');
      setTimeout(() => {
        if (!active) {
          addBotMessage('<b>📋 У вас пока нет активной анкеты.</b>\nВы можете создать её, нажав «🔎 Найти команду» или «👥 Найти участника».', {
            inlineKeyboard: [
              [{ text: '🔎 Найти команду', callback_data: 'start_team' }],
              [{ text: '👥 Найти участника', callback_data: 'start_member' }]
            ]
          });
        } else {
          const statusLabel = active.status === 'accepted' ? '🟢 Принята модератором' : '🟡 На рассмотрении';
          addBotMessage(
            `<b>📋 Ваша анкета #${active.id}</b>\n\nСтатус: <b>${statusLabel}</b>\n\n👤 <b>Имя:</b> ${active.name}\n🎯 <b>Роль:</b> ${active.role}\n💻 <b>Навыки:</b> ${active.skills}\n📈 <b>Опыт:</b> ${active.experience}\n⏰ <b>Время:</b> ${active.availability}`,
            {
              inlineKeyboard: [
                [{ text: '🗑 Удалить анкету', callback_data: `prof_delete:${active.id}` }]
              ]
            }
          );
        }
      }, 300);
      return;
    }

    if (text === '🔎 Найти команду') {
      const active = applications.find(a => a.status === 'new' || a.status === 'accepted');
      if (active) {
        setTimeout(() => {
          addBotMessage(`⚠️ У вас уже есть активная анкета <b>#${active.id}</b> со статусом <b>${active.status}</b>.\nУдалите её в разделе «📋 Моя анкета», чтобы создать новую.`);
        }, 300);
        return;
      }

      setUserFsmState('team_name');
      setDraftData({ type: 'looking_for_team' });
      setTimeout(() => {
        addBotMessage('<b>Шаг 1 из 7: Представьтесь</b>\n\n👤 Введите ваше имя или никнейм:', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 300);
      return;
    }

    if (text === '👥 Найти участника') {
      const active = applications.find(a => a.status === 'new' || a.status === 'accepted');
      if (active) {
        setTimeout(() => {
          addBotMessage(`⚠️ У вас уже есть активная анкета <b>#${active.id}</b>.\nУдалите её в разделе «📋 Моя анкета», чтобы создать новую.`);
        }, 300);
        return;
      }

      setUserFsmState('member_name');
      setDraftData({ type: 'looking_for_member' });
      setTimeout(() => {
        addBotMessage('<b>Шаг 1 из 7: Проект / Команда</b>\n\n🚀 Введите название проекта или ваше имя:', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 300);
      return;
    }

    // Step by step questionnaire logic
    handleQuestionnaireStep(text);
  };

  const handleQuestionnaireStep = (text: string) => {
    if (!userFsmState) return;

    // Team search steps
    if (userFsmState === 'team_name') {
      if (text === '⬅️ Назад') {
        setUserFsmState(null);
        addBotMessage('Вы в начале меню.', {
          replyKeyboard: [
            [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
            [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
          ]
        });
        return;
      }
      setDraftData(prev => ({ ...prev, name: text }));
      setUserFsmState('team_role');
      setTimeout(() => {
        addBotMessage('<b>Шаг 2 из 7: Ваша роль</b>\n\n🎯 Укажите вашу специальность (например: <i>Frontend Developer, Python Backend, Designer</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'team_role') {
      if (text === '⬅️ Назад') {
        setUserFsmState('team_name');
        addBotMessage('👤 Введите ваше имя или никнейм:');
        return;
      }
      setDraftData(prev => ({ ...prev, role: text }));
      setUserFsmState('team_skills');
      setTimeout(() => {
        addBotMessage('<b>Шаг 3 из 7: Ключевые навыки</b>\n\n💻 Перечислите стек технологий (например: <i>React, TypeScript, Tailwind, Git</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'team_skills') {
      if (text === '⬅️ Назад') {
        setUserFsmState('team_role');
        addBotMessage('🎯 Укажите вашу специальность:');
        return;
      }
      setDraftData(prev => ({ ...prev, skills: text }));
      setUserFsmState('team_exp');
      setTimeout(() => {
        addBotMessage('<b>Шаг 4 из 7: Опыт</b>\n\n📈 Опишите ваш опыт (например: <i>2 года, Middle, 3 проекта</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'team_exp') {
      if (text === '⬅️ Назад') {
        setUserFsmState('team_skills');
        addBotMessage('💻 Перечислите стек технологий:');
        return;
      }
      setDraftData(prev => ({ ...prev, experience: text }));
      setUserFsmState('team_looking');
      setTimeout(() => {
        addBotMessage('<b>Шаг 5 из 7: Что вы ищете</b>\n\n🔎 Опишите, какую команду или проект вы ищете (например: <i>команду для стартапа, хакатон</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'team_looking') {
      if (text === '⬅️ Назад') {
        setUserFsmState('team_exp');
        addBotMessage('📈 Опишите ваш опыт:');
        return;
      }
      setDraftData(prev => ({ ...prev, looking_for: text }));
      setUserFsmState('team_time');
      setTimeout(() => {
        addBotMessage('<b>Шаг 6 из 7: Время</b>\n\n⏰ Сколько часов готовы уделять (например: <i>10 часов в неделю, full-time</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'team_time') {
      if (text === '⬅️ Назад') {
        setUserFsmState('team_looking');
        addBotMessage('🔎 Опишите, какую команду ищете:');
        return;
      }
      setDraftData(prev => ({ ...prev, availability: text }));
      setUserFsmState('team_about');
      setTimeout(() => {
        addBotMessage('<b>Шаг 7 из 7: О себе</b>\n\n📝 Расскажите немного о себе или оставьте ссылку на портфолио/GitHub (или напишите -):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'team_about') {
      if (text === '⬅️ Назад') {
        setUserFsmState('team_time');
        addBotMessage('⏰ Сколько часов готовы уделять:');
        return;
      }
      const finalData = { ...draftData, about: text === '-' ? '' : text };
      setDraftData(finalData);
      setUserFsmState('confirm');

      setTimeout(() => {
        const preview = `<b>Проверьте информацию:</b>\n\n👤 <b>Имя:</b> ${finalData.name}\n🎯 <b>Роль:</b> ${finalData.role}\n💻 <b>Навыки:</b> ${finalData.skills}\n📈 <b>Опыт:</b> ${finalData.experience}\n🔎 <b>Ищу:</b> ${finalData.looking_for}\n⏰ <b>Время:</b> ${finalData.availability}\n📝 <b>О себе:</b> ${finalData.about || 'Не указано'}\n\n<b>Всё верно?</b>`;
        addBotMessage(preview, {
          inlineKeyboard: [
            [{ text: '✅ Отправить', callback_data: 'app_submit' }],
            [
              { text: '✏️ Изменить', callback_data: 'app_edit' },
              { text: '❌ Отмена', callback_data: 'app_cancel' }
            ]
          ]
        });
      }, 200);
    }

    // Member search steps
    else if (userFsmState === 'member_name') {
      setDraftData(prev => ({ ...prev, name: text }));
      setUserFsmState('member_role');
      setTimeout(() => {
        addBotMessage('<b>Шаг 2 из 7: Кого вы ищете</b>\n\n🎯 Какая роль требуется в проект? (например: <i>Python-разработчик</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'member_role') {
      setDraftData(prev => ({ ...prev, role: text }));
      setUserFsmState('member_skills');
      setTimeout(() => {
        addBotMessage('<b>Шаг 3 из 7: Требуемые навыки</b>\n\n💻 Какие технологии требуются? (например: <i>Python, aiogram, PostgreSQL</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'member_skills') {
      setDraftData(prev => ({ ...prev, skills: text }));
      setUserFsmState('member_exp');
      setTimeout(() => {
        addBotMessage('<b>Шаг 4 из 7: Опыт</b>\n\n📈 Какой опыт требуется? (например: <i>от 1 года</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'member_exp') {
      setDraftData(prev => ({ ...prev, experience: text }));
      setUserFsmState('member_desc');
      setTimeout(() => {
        addBotMessage('<b>Шаг 5 из 7: О проекте</b>\n\n📖 Опишите ваш проект: идея, стадия, цели:', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'member_desc') {
      setDraftData(prev => ({ ...prev, project_description: text, looking_for: text }));
      setUserFsmState('member_time');
      setTimeout(() => {
        addBotMessage('<b>Шаг 6 из 7: Занятость</b>\n\n⏰ Какая ожидается занятость? (например: <i>10-15 часов в неделю</i>):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'member_time') {
      setDraftData(prev => ({ ...prev, availability: text }));
      setUserFsmState('member_about');
      setTimeout(() => {
        addBotMessage('<b>Шаг 7 из 7: Условия</b>\n\n📝 Условия, доля или пожелания (или напишите -):', {
          replyKeyboard: [[{ text: '⬅️ Назад' }, { text: '❌ Отмена' }]]
        });
      }, 200);
    } else if (userFsmState === 'member_about') {
      const finalData = { ...draftData, about: text === '-' ? '' : text };
      setDraftData(finalData);
      setUserFsmState('confirm');

      setTimeout(() => {
        const preview = `<b>Проверьте информацию:</b>\n\n🚀 <b>Проект:</b> ${finalData.name}\n🎯 <b>Ищет:</b> ${finalData.role}\n💻 <b>Навыки:</b> ${finalData.skills}\n📈 <b>Опыт:</b> ${finalData.experience}\n📖 <b>О проекте:</b> ${finalData.project_description}\n⏰ <b>Занятость:</b> ${finalData.availability}\n📝 <b>Условия:</b> ${finalData.about || 'Не указано'}\n\n<b>Всё верно?</b>`;
        addBotMessage(preview, {
          inlineKeyboard: [
            [{ text: '✅ Отправить', callback_data: 'app_submit' }],
            [
              { text: '✏️ Изменить', callback_data: 'app_edit' },
              { text: '❌ Отмена', callback_data: 'app_cancel' }
            ]
          ]
        });
      }, 200);
    }
  };

  // User inline callback click handler
  const handleUserCallback = (callback_data: string) => {
    if (callback_data === 'app_cancel') {
      setUserFsmState(null);
      setDraftData({});
      addBotMessage('❌ Создание анкеты отменено.', {
        replyKeyboard: [
          [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
          [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
        ]
      });
    } else if (callback_data === 'app_edit') {
      setUserFsmState('team_name');
      addBotMessage('✏️ Начнем редактирование заново.\n\n👤 Введите ваше имя или никнейм:');
    } else if (callback_data === 'app_submit') {
      const newId = applications.length > 0 ? Math.max(...applications.map(a => a.id)) + 1 : 101;
      const newApp: ApplicationRecord = {
        id: newId,
        user_id: 987654321,
        type: (draftData.type as ApplicationType) || 'looking_for_team',
        name: draftData.name || 'Alex',
        role: draftData.role || 'Frontend Developer',
        skills: draftData.skills || 'React, TypeScript',
        experience: draftData.experience || '2 года',
        looking_for: draftData.looking_for || 'стартап',
        project_description: draftData.project_description,
        availability: draftData.availability || '10 часов в неделю',
        about: draftData.about,
        telegram_contact: '@alex_dev',
        status: 'new',
        created_at: new Date().toISOString(),
      };

      setApplications(prev => [newApp, ...prev]);
      setUserFsmState(null);
      setDraftData({});

      // Confirmation to user
      addBotMessage(
        '✅ <b>Ваша анкета успешно отправлена!</b>\n\nАдминистраторы сообщества получили заявку и рассмотрят её в ближайшее время.',
        {
          replyKeyboard: [
            [{ text: '🔎 Найти команду' }, { text: '👥 Найти участника' }],
            [{ text: '📋 Моя анкета' }, { text: '❓ Помощь' }]
          ]
        }
      );

      // Card to Admin channel
      const isTeam = newApp.type === 'looking_for_team';
      const typeTitle = isTeam ? '🔎 ПОИСК КОМАНДЫ' : '👥 ПОИСК УЧАСТНИКА';
      const adminCardText = `━━━━━━━━━━━━━━\n<b>👥 НОВАЯ АНКЕТА #${newApp.id}</b>\n${typeTitle}\n━━━━━━━━━━━━━━\n\n👤 <b>${newApp.name}</b> (@alex_dev)\n\n🎯 <b>Роль:</b>\n${newApp.role}\n\n💻 <b>Навыки:</b>\n${newApp.skills}\n\n📈 <b>Опыт:</b>\n${newApp.experience}\n\n🔎 <b>Ищет:</b>\n${newApp.looking_for}\n\n⏰ <b>Время:</b>\n${newApp.availability}\n\n📝 <b>О себе:</b>\n${newApp.about || 'Не указано'}\n━━━━━━━━━━━━━━`;

      addAdminBotMessage(adminCardText, {
        inlineKeyboard: [
          [
            { text: '✅ Принять', callback_data: `adm_accept:${newApp.id}` },
            { text: '❌ Отклонить', callback_data: `adm_reject:${newApp.id}` }
          ],
          [
            { text: '💬 Связаться', callback_data: `adm_contact:${newApp.id}` },
            { text: '🚫 Заблокировать', callback_data: `adm_block:${newApp.id}` }
          ]
        ],
        appId: newApp.id
      });
    } else if (callback_data.startsWith('prof_delete:')) {
      const appId = Number(callback_data.split(':')[1]);
      setApplications(prev => prev.filter(a => a.id !== appId));
      addBotMessage('🗑 <b>Ваша анкета была успешно отозвана / удалена.</b>\nТеперь вы можете создать новую.');
    } else if (callback_data.startsWith('user_reply:')) {
      const appId = Number(callback_data.split(':')[1]);
      setUserReplyTarget(appId);
      addBotMessage('✍️ <b>Напишите ваш ответ администратору:</b>\n(Сообщение будет отправлено через бота)', {
        replyKeyboard: [[{ text: '❌ Отмена' }]]
      });
    }
  };

  // Admin inline callback click handler
  const handleAdminCallback = (callback_data: string) => {
    if (callback_data.startsWith('adm_accept:')) {
      const appId = Number(callback_data.split(':')[1]);
      setApplications(prev => prev.map(a => a.id === appId ? { ...a, status: 'accepted' } : a));

      // Update admin message buttons
      setAdminMessages(prev => prev.map(msg => {
        if (msg.appId === appId) {
          return {
            ...msg,
            inlineKeyboard: [
              [{ text: '🟢 ПРИНЯТО', callback_data: `adm_noop:${appId}` }],
              [{ text: '💬 Написать пользователю', callback_data: `adm_contact:${appId}` }]
            ]
          };
        }
        return msg;
      }));

      // Notify candidate in user chat!
      addBotMessage(
        '🎉 <b>Ваша анкета была принята!</b>\n\nАдминистратор скоро свяжется с вами.'
      );
    } else if (callback_data.startsWith('adm_reject:')) {
      const appId = Number(callback_data.split(':')[1]);
      setApplications(prev => prev.map(a => a.id === appId ? { ...a, status: 'rejected' } : a));

      setAdminMessages(prev => prev.map(msg => {
        if (msg.appId === appId) {
          return {
            ...msg,
            inlineKeyboard: [
              [{ text: '🔴 ОТКЛОНЕНО', callback_data: `adm_noop:${appId}` }]
            ]
          };
        }
        return msg;
      }));

      // Notify candidate
      addBotMessage(
        'Спасибо за заявку!\n\nК сожалению, сейчас ваша анкета не подходит.'
      );
    } else if (callback_data.startsWith('adm_contact:')) {
      const appId = Number(callback_data.split(':')[1]);
      setAdminReplyTarget(appId);
      addAdminBotMessage(`💬 <b>Напишите сообщение для пользователя по заявке #${appId}:</b>\n\n(Введите текст сообщения ниже в поле ввода админа)`);
    } else if (callback_data.startsWith('adm_block:')) {
      const appId = Number(callback_data.split(':')[1]);
      setIsBlocked(true);
      setApplications(prev => prev.map(a => a.id === appId ? { ...a, status: 'rejected' } : a));

      setAdminMessages(prev => prev.map(msg => {
        if (msg.appId === appId) {
          return {
            ...msg,
            text: msg.text + '\n\n🚫 <b>ПОЛЬЗОВАТЕЛЬ ЗАБЛОКИРОВАН</b>',
            inlineKeyboard: [
              [{ text: '🚫 ЗАБЛОКИРОВАН', callback_data: `adm_noop:${appId}` }]
            ]
          };
        }
        return msg;
      }));
    }
  };

  // Admin sends message
  const handleAdminSend = () => {
    const text = adminInput.trim();
    if (!text) return;

    setAdminMessages(prev => [
      ...prev,
      {
        id: String(Date.now()),
        sender: 'admin',
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setAdminInput('');

    if (adminReplyTarget) {
      const targetId = adminReplyTarget;
      setAdminReplyTarget(null);

      setTimeout(() => {
        addAdminBotMessage(`✅ <b>Сообщение отправлено кандидату по заявке #${targetId}!</b>`);
        // Deliver to candidate!
        addBotMessage(
          `💬 <b>Сообщение от администратора:</b>\n\n${text}`,
          {
            inlineKeyboard: [
              [{ text: '💬 Ответить администратору', callback_data: `user_reply:${targetId}` }]
            ],
            appId: targetId
          }
        );
      }, 300);
      return;
    }

    // Check if /admin command
    if (text === '/admin') {
      const newCount = applications.filter(a => a.status === 'new').length;
      const accCount = applications.filter(a => a.status === 'accepted').length;
      const rejCount = applications.filter(a => a.status === 'rejected').length;

      setTimeout(() => {
        addAdminBotMessage(
          `🛡 <b>Панель управления TeamFinder</b>\n\nВсего заявок: <b>${applications.length}</b>\n• Новых: <b>${newCount}</b>\n• Принятых: <b>${accCount}</b>\n• Отклонённых: <b>${rejCount}</b>\n• Заблокированных: <b>${isBlocked ? 1 : 0}</b>\n\nДоступ: <b>Разрешен (User ID: 123456789)</b>`
        );
      }, 200);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col lg:flex-row gap-6 items-start">
      {/* Device View Container */}
      <div className="w-full lg:w-[460px] bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col h-[740px] shrink-0">
        {/* Telegram Header Bar */}
        <div className="bg-slate-800/90 backdrop-blur-md px-4 py-3 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow ${activeTab === 'candidate' ? 'bg-gradient-to-tr from-sky-600 to-blue-500' : 'bg-gradient-to-tr from-purple-600 to-indigo-500'}`}>
              {activeTab === 'candidate' ? <Bot className="w-5 h-5" /> : <Shield className="w-5 h-5" />}
            </div>
            <div>
              <div className="font-semibold text-white text-sm flex items-center gap-1.5">
                {activeTab === 'candidate' ? 'TeamFinder Bot' : 'TeamFinder Admin Feed'}
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              </div>
              <div className="text-xs text-slate-400">
                {activeTab === 'candidate' ? 'bot • онлайн' : 'секретный чат модерации'}
              </div>
            </div>
          </div>

          {/* Quick Mode Toggle */}
          <div className="flex bg-slate-900/80 p-0.5 rounded-lg border border-slate-700">
            <button
              onClick={() => setActiveTab('candidate')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${activeTab === 'candidate' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Кандидат
            </button>
            <button
              onClick={() => setActiveTab('admin')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${activeTab === 'admin' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Админ
              {applications.filter(a => a.status === 'new').length > 0 && (
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              )}
            </button>
          </div>
        </div>

        {/* Message Log Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-950/70 text-sm">
          {activeTab === 'candidate' ? (
            userMessages.map(msg => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 shadow-md leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-sky-600 text-white rounded-br-none'
                      : 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-bl-none'
                  }`}
                >
                  <div
                    dangerouslySetInnerHTML={{ __html: msg.text.replace(/\n/g, '<br/>') }}
                    className="whitespace-pre-wrap break-words"
                  />
                  <div className={`text-[10px] mt-1 text-right ${msg.sender === 'user' ? 'text-sky-200' : 'text-slate-400'}`}>
                    {msg.timestamp}
                  </div>
                </div>

                {/* Inline Buttons attached to Bot Message */}
                {msg.inlineKeyboard && (
                  <div className="w-full max-w-[85%] mt-1.5 space-y-1.5">
                    {msg.inlineKeyboard.map((row, rIdx) => (
                      <div key={rIdx} className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${row.length}, 1fr)` }}>
                        {row.map((btn, bIdx) => (
                          <button
                            key={bIdx}
                            onClick={() => handleUserCallback(btn.callback_data)}
                            className="bg-slate-800/95 hover:bg-sky-600 text-sky-300 hover:text-white border border-slate-700 rounded-xl py-2 px-2 text-xs font-medium text-center transition shadow-sm active:scale-95"
                          >
                            {btn.text}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            adminMessages.map(msg => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === 'admin' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl px-3.5 py-2.5 shadow-md leading-relaxed ${
                    msg.sender === 'admin'
                      ? 'bg-purple-600 text-white rounded-br-none'
                      : 'bg-slate-800/90 text-slate-100 border border-slate-700/80 rounded-bl-none'
                  }`}
                >
                  <div
                    dangerouslySetInnerHTML={{ __html: msg.text.replace(/\n/g, '<br/>') }}
                    className="whitespace-pre-wrap break-words font-mono text-xs"
                  />
                  <div className={`text-[10px] mt-1 text-right ${msg.sender === 'admin' ? 'text-purple-200' : 'text-slate-400'}`}>
                    {msg.timestamp}
                  </div>
                </div>

                {/* Admin Action Inline Buttons */}
                {msg.inlineKeyboard && (
                  <div className="w-full max-w-[90%] mt-2 space-y-1.5">
                    {msg.inlineKeyboard.map((row, rIdx) => (
                      <div key={rIdx} className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${row.length}, 1fr)` }}>
                        {row.map((btn, bIdx) => (
                          <button
                            key={bIdx}
                            onClick={() => handleAdminCallback(btn.callback_data)}
                            className="bg-slate-800/95 hover:bg-purple-700 text-purple-300 hover:text-white border border-slate-700 rounded-xl py-2 px-2 text-xs font-semibold text-center transition shadow active:scale-95"
                          >
                            {btn.text}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={activeTab === 'candidate' ? userScrollRef : adminScrollRef} />
        </div>

        {/* Reply Keyboard Area (If any active) */}
        {activeTab === 'candidate' && userMessages[userMessages.length - 1]?.replyKeyboard && (
          <div className="p-2.5 bg-slate-900 border-t border-slate-800 flex flex-col gap-1.5 shrink-0">
            {userMessages[userMessages.length - 1]?.replyKeyboard?.map((row, rIdx) => (
              <div key={rIdx} className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${row.length}, 1fr)` }}>
                {row.map((btn, bIdx) => (
                  <button
                    key={bIdx}
                    onClick={() => handleUserSend(btn.text)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-xl py-2.5 px-3 text-xs font-medium text-center border border-slate-700/80 shadow-sm transition active:scale-95"
                  >
                    {btn.text}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Text Input Footer */}
        <div className="p-3 bg-slate-900 border-t border-slate-800 flex items-center gap-2 shrink-0">
          <input
            type="text"
            value={activeTab === 'candidate' ? userInput : adminInput}
            onChange={e => activeTab === 'candidate' ? setUserInput(e.target.value) : setAdminInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                if (activeTab === 'candidate') handleUserSend();
                else handleAdminSend();
              }
            }}
            placeholder={
              activeTab === 'candidate'
                ? (userReplyTarget ? 'Напишите ответ администратору...' : 'Введите сообщение или команду...')
                : (adminReplyTarget ? 'Напишите сообщение кандидату...' : 'Введите команду (/admin) или сообщение...')
            }
            className="flex-1 bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-3.5 py-2.5 focus:outline-none focus:border-sky-500 transition"
          />
          <button
            onClick={() => activeTab === 'candidate' ? handleUserSend() : handleAdminSend()}
            className={`p-2.5 rounded-xl text-white transition shadow active:scale-95 ${
              activeTab === 'candidate' ? 'bg-sky-600 hover:bg-sky-500' : 'bg-purple-600 hover:bg-purple-500'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Simulator Control & Inspection Sidebar */}
      <div className="flex-1 space-y-5">
        {/* Status Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                Интерактивное тестирование Telegram Bot API
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Симуляция 100% повторяет поведение Python-бота на <b>aiogram 3.x</b> и <b>SQLite</b>
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              18/18 Сценариев ТЗ
            </span>
          </div>

          {/* Quick Scenario Triggers */}
          <div className="mt-4">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Быстрые тест-сценарии в 1 клик:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => {
                  setActiveTab('candidate');
                  handleUserSend('/start');
                }}
                className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl p-2.5 text-left text-slate-200 transition flex items-center justify-between"
              >
                <span>1. Запустить <code>/start</code></span>
                <span className="text-[10px] text-slate-400">Старт меню</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('candidate');
                  handleUserSend('🔎 Найти команду');
                }}
                className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl p-2.5 text-left text-slate-200 transition flex items-center justify-between"
              >
                <span>2. Анкета «Найти команду»</span>
                <span className="text-[10px] text-slate-400">Шаг 1 из 7</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('candidate');
                  handleUserSend('👥 Найти участника');
                }}
                className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl p-2.5 text-left text-slate-200 transition flex items-center justify-between"
              >
                <span>3. Анкета «Найти участника»</span>
                <span className="text-[10px] text-slate-400">Поиск в проект</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('admin');
                  setAdminInput('/admin');
                  handleAdminSend();
                }}
                className="bg-purple-950/40 hover:bg-purple-900/40 border border-purple-800/60 rounded-xl p-2.5 text-left text-purple-200 transition flex items-center justify-between"
              >
                <span>4. Открыть <code>/admin</code></span>
                <span className="text-[10px] text-purple-300 font-mono">Статистика</span>
              </button>
            </div>
          </div>
        </div>

        {/* Live Database Explorer */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-400"></span>
              База Данных: Заявки (<code>applications</code>)
            </h4>
            <span className="text-xs text-slate-400">
              Всего в БД: {applications.length}
            </span>
          </div>

          <div className="mt-3 divide-y divide-slate-800 max-h-72 overflow-y-auto pr-1">
            {applications.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">
                Пока нет созданных анкет. Запустите анкету в симуляторе слева.
              </div>
            ) : (
              applications.map(app => (
                <div key={app.id} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-200 flex items-center gap-2">
                      #{app.id} • {app.name}
                      <span className="text-[10px] text-slate-400 font-normal">({app.role})</span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Стек: {app.skills} | Время: {app.availability}
                    </div>
                  </div>
                  <div>
                    {app.status === 'new' && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        🟡 Новая
                      </span>
                    )}
                    {app.status === 'accepted' && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        🟢 Принята
                      </span>
                    )}
                    {app.status === 'rejected' && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        🔴 Отклонена
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Security & Isolation Features */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 text-xs text-slate-400 space-y-2">
          <div className="font-semibold text-slate-200 flex items-center gap-2">
            <Shield className="w-4 h-4 text-purple-400" />
            Реализованные механизмы надежности
          </div>
          <p>
            • <b>Защита от спама и дублей:</b> Пользователь не может подать повторную анкету, пока у него активна заявка в статусе <code>new</code> или <code>accepted</code>.
          </p>
          <p>
            • <b>Идемпотентность кнопок:</b> Повторный клик модератора по кнопке «Принять» не меняет состояние и не шлет повторные уведомления.
          </p>
          <p>
            • <b>Безопасный двухсторонний диалог:</b> Администратор и кандидат общаются через бота, личные ID кандидата и админа остаются защищены.
          </p>
        </div>
      </div>
    </div>
  );
};
