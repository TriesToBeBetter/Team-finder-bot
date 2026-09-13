import React, { useState } from 'react';
import { Terminal, Copy, Check, ExternalLink, ShieldCheck, Key, Settings, Server } from 'lucide-react';

export const DeploymentGuide: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const steps = [
    {
      title: "1. Получение токена бота в Telegram",
      desc: "Создайте бота через официального @BotFather и сохраните HTTP API токен.",
      command: `/newbot\n# Введите имя бота: TeamFinder Community\n# Введите юзернейм: my_teamfinder_bot\n# BotFather выдаст токен вида: 7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
    },
    {
      title: "2. Узнайте свой числовой Telegram User ID",
      desc: "Напишите боту @userinfobot или @getmyid_bot, чтобы скопировать ваш числовой ID (например 123456789) для ADMIN_IDS.",
      command: `ADMIN_IDS=123456789`
    },
    {
      title: "3. Клонирование и установка на сервере VPS (Ubuntu/Debian)",
      desc: "Подключитесь по SSH, установите Python 3 и зависимости:",
      command: `sudo apt update && sudo apt install -y python3 python3-pip python3-venv git\ngit clone <YOUR_REPO> /opt/teamfinder\ncd /opt/teamfinder\npython3 -m venv venv\nsource venv/bin/activate\npip install -r requirements.txt\ncp .env.example .env\nnano .env`
    },
    {
      title: "4. Настройка автозапуска через systemd",
      desc: "Создайте службу /etc/systemd/system/teamfinder.service для круглосуточной работы бота и перезапуска при сбоях:",
      command: `sudo tee /etc/systemd/system/teamfinder.service > /dev/null << 'EOF'
[Unit]
Description=TeamFinder Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/teamfinder
ExecStart=/opt/teamfinder/venv/bin/python /opt/teamfinder/main.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/teamfinder/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable teamfinder.service
sudo systemctl start teamfinder.service
sudo systemctl status teamfinder.service`
    },
    {
      title: "5. Просмотр логов в реальном времени",
      desc: "Команда для мониторинга событий бота на сервере:",
      command: `sudo journalctl -u teamfinder.service -f`
    }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
          <Server className="w-6 h-6 text-purple-400" />
          Инструкция по развертыванию на VPS / сервере
        </h2>
        <p className="text-sm text-slate-400 mt-2">
          Пошаговое руководство для запуска в продакшене с гарантией бесперебойной работы 24/7.
        </p>
      </div>

      <div className="space-y-4">
        {steps.map((step, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-slate-800 text-sky-400 flex items-center justify-center text-xs">
                    {idx + 1}
                  </span>
                  {step.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {step.desc}
                </p>
              </div>
              <button
                onClick={() => copyToClipboard(step.command, idx)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition flex items-center gap-1 text-xs"
              >
                {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedIndex === idx ? 'Скопировано' : 'Копировать'}</span>
              </button>
            </div>

            <div className="mt-3 bg-slate-950 rounded-xl p-3 border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
              <pre>{step.command}</pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
