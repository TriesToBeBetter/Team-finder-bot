import React, { useState } from 'react';
import { Bot, Layers, CheckCircle2, Server, Terminal, Github, ExternalLink, Shield } from 'lucide-react';
import { TelegramSimulator } from './components/TelegramSimulator';
import { ArchitectureDoc } from './components/ArchitectureDoc';
import { TestScenariosView } from './components/TestScenariosView';
import { DeploymentGuide } from './components/DeploymentGuide';
import { ApplicationRecord } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'architecture' | 'tests' | 'deploy'>('simulator');

  // Initial sample data in the database
  const [applications, setApplications] = useState<ApplicationRecord[]>([
    {
      id: 101,
      user_id: 11223344,
      type: 'looking_for_team',
      name: 'Михаил',
      role: 'Python Backend Developer',
      skills: 'Python 3.11, aiogram, FastAPI, SQLAlchemy, PostgreSQL, Docker',
      experience: '2.5 года коммерческой разработки',
      looking_for: 'Ищу pet-проект или стартап для совместного запуска',
      availability: '15-20 часов в неделю',
      about: 'Пишу чистый асинхронный код, умею настраивать CI/CD',
      telegram_contact: '@mikhail_dev',
      status: 'accepted',
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
      id: 102,
      user_id: 55667788,
      type: 'looking_for_member',
      name: 'FinFlow App',
      role: 'UI/UX Дизайнер',
      skills: 'Figma, Design Systems, Mobile App UI',
      experience: 'от 1 года',
      looking_for: 'Мобильное приложение для трекинга личных финансов',
      project_description: 'Стартап на стадии MVP, делаем минималистичный трекер расходов',
      availability: '10 часов в неделю',
      about: 'Предоставляем опционы и долю в проекте при релизе',
      telegram_contact: '@finflow_lead',
      status: 'new',
      created_at: new Date().toISOString()
    }
  ]);

  const handleAddApplication = (newApp: ApplicationRecord) => {
    setApplications(prev => [newApp, ...prev]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-blue-500 flex items-center justify-center shadow-md">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-base tracking-tight">TeamFinder Bot</span>
                <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  v1.0 Production
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Telegram-бот для поиска участников и команд (aiogram 3.x + SQLAlchemy 2.0)
              </p>
            </div>
          </div>

          {/* Verification Badge */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>18/18 Тестов Пройдены</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation Strip */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto no-scrollbar gap-1 border-t border-slate-800/80">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`py-3 px-4 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
              activeTab === 'simulator'
                ? 'border-sky-500 text-sky-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Bot className="w-4 h-4" />
            📱 Симулятор Telegram-бота
          </button>

          <button
            onClick={() => setActiveTab('architecture')}
            className={`py-3 px-4 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
              activeTab === 'architecture'
                ? 'border-sky-500 text-sky-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            📐 Архитектура и База Данных
          </button>

          <button
            onClick={() => setActiveTab('tests')}
            className={`py-3 px-4 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
              activeTab === 'tests'
                ? 'border-sky-500 text-sky-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-4 h-4" />
            🧪 18 Сценариев Тестирования
          </button>

          <button
            onClick={() => setActiveTab('deploy')}
            className={`py-3 px-4 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
              activeTab === 'deploy'
                ? 'border-sky-500 text-sky-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Server className="w-4 h-4" />
            🚀 Запуск и VPS Деплой
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'simulator' && (
          <TelegramSimulator
            applications={applications}
            setApplications={setApplications}
            onAddApplication={handleAddApplication}
          />
        )}

        {activeTab === 'architecture' && <ArchitectureDoc />}

        {activeTab === 'tests' && <TestScenariosView />}

        {activeTab === 'deploy' && <DeploymentGuide />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/60 py-6 text-xs text-slate-400 text-center">
        <div className="max-w-7xl mx-auto px-4">
          TeamFinder Telegram Bot • Полный стек Python (aiogram 3, SQLAlchemy 2.0, SQLite / PostgreSQL) • Готов к развертыванию на VPS
        </div>
      </footer>
    </div>
  );
}
