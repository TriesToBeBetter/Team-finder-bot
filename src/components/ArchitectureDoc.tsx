import React from 'react';
import { Database, Server, Workflow, ShieldCheck, Cpu, Code2, CheckCircle2 } from 'lucide-react';

export const ArchitectureDoc: React.FC = () => {
  return (
    <div className="w-full max-w-5xl mx-auto space-y-8">
      {/* Overview Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
          <Server className="w-6 h-6 text-sky-400" />
          Архитектура TeamFinder Bot
        </h2>
        <p className="text-sm text-slate-400 mt-2 leading-relaxed">
          Проект построен по модульной слоистой архитектуре на базе <b>Python 3.10+</b>, <b>aiogram 3.x</b> и <b>SQLAlchemy 2.0 async</b> с полной изоляцией слоёв (обработчики, бизнес-логика, доступ к данным, промежуточные слои).
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <div className="font-semibold text-white text-sm flex items-center gap-2">
              <Workflow className="w-4 h-4 text-sky-400" />
              Aiogram 3.x Dispatcher
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Роутерная структура (Routers) для разделения логики кандидатов, анкет, админки и чата.
            </p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <div className="font-semibold text-white text-sm flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-400" />
              SQLAlchemy 2.0 Async
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Поддержка SQLite (локально) и PostgreSQL (на сервере) простой сменой <code>DATABASE_URL</code>.
            </p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <div className="font-semibold text-white text-sm flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              RBAC & ID Security
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Проверка прав администратора строго по числовому <code>telegram_user_id</code> (защита от смены @username).
            </p>
          </div>
        </div>
      </div>

      {/* Database Schema Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-emerald-400" />
          Структура базы данных (ORM Models)
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Модели определены в <code>bot/database/models.py</code> с каскадными связями и внешними ключами:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-xs font-mono">
          {/* Table: users */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="text-emerald-400 font-bold text-sm">Table: users</div>
            <div className="text-slate-300">
              • <b>id</b>: Integer (PK, autoincrement)<br />
              • <b>telegram_user_id</b>: BigInteger (unique, indexed)<br />
              • <b>username</b>: String(64) (nullable)<br />
              • <b>first_name</b>: String(128)<br />
              • <b>last_name</b>: String(128) (nullable)<br />
              • <b>is_blocked</b>: Boolean (default=False)<br />
              • <b>created_at</b>: DateTime(timezone=True)<br />
              • <b>updated_at</b>: DateTime(timezone=True)
            </div>
          </div>

          {/* Table: applications */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="text-sky-400 font-bold text-sm">Table: applications</div>
            <div className="text-slate-300">
              • <b>id</b>: Integer (PK, autoincrement)<br />
              • <b>user_id</b>: ForeignKey('users.id')<br />
              • <b>type</b>: Enum('looking_for_team', 'looking_for_member')<br />
              • <b>status</b>: Enum('new', 'accepted', 'rejected', 'cancelled')<br />
              • <b>name</b>: String(128)<br />
              • <b>role</b>: String(128)<br />
              • <b>skills</b>: Text<br />
              • <b>experience</b>: String(128)<br />
              • <b>looking_for</b>: Text<br />
              • <b>availability</b>: String(128)<br />
              • <b>about</b>: Text (nullable)<br />
              • <b>reviewed_by_admin_id</b>: BigInteger (nullable)
            </div>
          </div>

          {/* Table: admin_messages */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="text-purple-400 font-bold text-sm">Table: admin_messages (Relay Chat)</div>
            <div className="text-slate-300">
              • <b>id</b>: Integer (PK, autoincrement)<br />
              • <b>application_id</b>: ForeignKey('applications.id')<br />
              • <b>sender_type</b>: Enum('admin', 'user')<br />
              • <b>sender_id</b>: BigInteger (Telegram user ID)<br />
              • <b>recipient_id</b>: BigInteger (Telegram user ID)<br />
              • <b>text</b>: Text<br />
              • <b>created_at</b>: DateTime(timezone=True)
            </div>
          </div>

          {/* Table: audit_logs */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="text-amber-400 font-bold text-sm">Table: audit_logs</div>
            <div className="text-slate-300">
              • <b>id</b>: Integer (PK, autoincrement)<br />
              • <b>actor_id</b>: BigInteger (admin or system)<br />
              • <b>action</b>: String(64)<br />
              • <b>entity_type</b>: String(64)<br />
              • <b>entity_id</b>: Integer<br />
              • <b>details</b>: JSON / Text<br />
              • <b>created_at</b>: DateTime(timezone=True)
            </div>
          </div>
        </div>
      </div>

      {/* Telegram API Methods */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Code2 className="w-5 h-5 text-sky-400" />
          Используемые Telegram Bot API методы
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 text-xs">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-sky-300 font-mono">bot.send_message(...)</div>
            <div className="text-slate-400 mt-1">Отправка анкет в админ-чат, уведомление кандидатов, relay-чат.</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-sky-300 font-mono">callback.message.edit_text(...)</div>
            <div className="text-slate-400 mt-1">Обновление статуса в карточке модератора (замена кнопок на 🟢 ПРИНЯТО).</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-sky-300 font-mono">callback.answer(..., show_alert=True)</div>
            <div className="text-slate-400 mt-1">Всплывающие push-уведомления администратору и защита от повторных кликов.</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-sky-300 font-mono">bot.delete_webhook(...)</div>
            <div className="text-slate-400 mt-1">Сброс накопившихся старых апдейтов (drop_pending_updates=True) при рестарте.</div>
          </div>
        </div>
      </div>
    </div>
  );
};
