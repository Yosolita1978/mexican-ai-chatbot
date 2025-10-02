import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Image from 'next/image';
import { agentChat, clearAgentMemory } from '@/lib/api';
import { translations, detectLanguage, Language } from '@/lib/translations';

export default function Home() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<Language>('en');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadingMessages = {
    en: [
      "🔍 Searching García family recipes...",
      "📖 Consulting the recipe collection...",
      "👨‍🍳 Preparing your answer...",
      "✨ Almost ready..."
    ],
    es: [
      "🔍 Buscando en las recetas García...",
      "📖 Consultando la colección familiar...",
      "👨‍🍳 Preparando tu respuesta...",
      "✨ Casi listo..."
    ]
  };

  useEffect(() => {
    setLanguage(detectLanguage());
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      setLoadingMessage(0);
      interval = setInterval(() => {
        setLoadingMessage(prev => {
          const maxIndex = loadingMessages[language].length - 1;
          return prev < maxIndex ? prev + 1 : maxIndex;
        });
      }, 1800);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading, language]);

  const t = translations[language];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    const userMessage = query.trim();
    setQuery('');
    setError(null);

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await agentChat(userMessage);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    } catch (err) {
      console.error('Error chatting with agent:', err);
      setError('Failed to connect to recipe service.');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '¡Ay no! I ran into a little problem. Can you try asking that again, mijo?'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuery = (queryText: string) => {
    setQuery(queryText);
    setSidebarOpen(false);
  };

  const handleClearConversation = async () => {
    try {
      await clearAgentMemory();
      setMessages([]);
      setError(null);
      setSidebarOpen(false);
    } catch (err) {
      console.error('Error clearing conversation:', err);
    }
  };

  const formatMessage = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, index) => {
      // Check for video format: - VIDEO:XXXXX
      if (line.trim().startsWith('- VIDEO:')) {
        const videoId = line.trim().replace('- VIDEO:', '');
        return (
          <div key={index} className="my-3 sm:my-4">
            <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
              <iframe
                className="absolute top-0 left-0 w-full h-full rounded-lg"
                src={`https://www.youtube.com/embed/${videoId}`}
                title="YouTube video"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        );
      }

      // Check for markdown image format: ![alt](url)
      const imageMatch = line.match(/!\[([^\]]*)\]\(([^)]+)\)/);
      if (imageMatch) {
        const altText = imageMatch[1];
        const imageUrl = imageMatch[2];
        return (
          <div key={index} className="my-3 sm:my-4">
            <img
              src={imageUrl}
              alt={altText}
              className="rounded-lg max-w-full h-auto shadow-md"
              loading="lazy"
            />
          </div>
        );
      }

      if (line.startsWith('**') && line.endsWith('**')) {
        const text = line.replace(/\*\*/g, '');
        return <h3 key={index} className="text-base sm:text-lg font-bold text-turkey-red mt-3 sm:mt-4 mb-2">{text}</h3>;
      }
      if (line.startsWith('*') && line.endsWith('*')) {
        const text = line.replace(/\*/g, '');
        return <p key={index} className="text-xs sm:text-sm text-oxford-blue opacity-75 mb-2">{text}</p>;
      }
      if (line === '---') {
        return <hr key={index} className="my-3 sm:my-4 border-fulvous" />;
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index} className="mb-2 text-sm sm:text-base">{line}</p>;
    });
  };

  return (
    <>
      <Head>
        <title>{`${t.title} - ${t.subtitle}`}</title>
        <meta name="description" content="Authentic Mexican recipes from the García family" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <link rel="icon" href="/logo.png" />
      </Head>

      <div className="flex h-screen bg-ghost-white overflow-hidden">
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 xl:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed xl:relative
          top-0 left-0 h-full
          w-80 sm:w-96
          bg-oxford-blue text-cornsilk 
          flex flex-col 
          border-r-4 border-fulvous
          transform transition-transform duration-300 ease-in-out
          z-50
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full xl:translate-x-0'}
        `}>
          {/* Close button (mobile/tablet only) */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="xl:hidden absolute top-4 right-4 text-cornsilk hover:text-fulvous z-10"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Logo Header */}
          <div className="p-4 sm:p-6 border-b-2 border-fulvous">
            <div className="flex items-center gap-3 mb-4">
              <Image
                src="/logo.png"
                alt={t.title}
                width={50}
                height={50}
                className="rounded-lg sm:w-[60px] sm:h-[60px]"
              />
              <div>
                <h1 className="text-lg sm:text-xl font-bold">{t.title}</h1>
                <p className="text-xs text-fulvous">{t.subtitle}</p>
              </div>
            </div>

            {/* Language Toggle */}
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setLanguage('en')}
                className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-semibold transition-colors ${language === 'en'
                    ? 'bg-fulvous text-white'
                    : 'bg-oxford-blue text-cornsilk border border-fulvous hover:bg-turkey-red'
                  }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('es')}
                className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-semibold transition-colors ${language === 'es'
                    ? 'bg-fulvous text-white'
                    : 'bg-oxford-blue text-cornsilk border border-fulvous hover:bg-turkey-red'
                  }`}
              >
                Español
              </button>
            </div>

            {/* Clear Conversation Button */}
            {messages.length > 0 && (
              <button
                onClick={handleClearConversation}
                className="w-full mt-4 py-2.5 px-3 rounded-lg text-sm font-semibold bg-turkey-red text-white hover:bg-fulvous transition-colors"
              >
                🧹 Clear Chat
              </button>
            )}
          </div>

          {/* Signature Recipe Buttons */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <h2 className="text-xs sm:text-sm font-bold text-fulvous mb-4 uppercase tracking-wide">
              {t.signatureRecipes}
            </h2>
            <div className="space-y-3">
              <button
                onClick={() => handleQuickQuery(t.queryPozole)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors min-h-[60px] active:scale-95"
              >
                <div className="font-bold text-white text-sm sm:text-base">{t.pozole}</div>
                <div className="text-xs text-cornsilk mt-1">{t.pozoleDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.queryFajitas)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors min-h-[60px] active:scale-95"
              >
                <div className="font-bold text-white text-sm sm:text-base">{t.fajitas}</div>
                <div className="text-xs text-cornsilk mt-1">{t.fajitasDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.queryTuna)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors min-h-[60px] active:scale-95"
              >
                <div className="font-bold text-white text-sm sm:text-base">{t.tuna}</div>
                <div className="text-xs text-cornsilk mt-1">{t.tunaDesc}</div>
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 sm:p-6 border-t-2 border-fulvous">
            <p className="text-xs text-cornsilk text-center">
              {t.footerText}
            </p>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col min-w-0">
          {/* Chat Header */}
          <header className="bg-white border-b-2 border-cornsilk p-3 sm:p-4 shadow-sm flex items-center gap-3">
            {/* Hamburger Menu (mobile/tablet only) */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="xl:hidden text-oxford-blue hover:text-turkey-red p-2"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <div className="flex-1 min-w-0">
              <h2 className="text-lg sm:text-xl font-bold text-oxford-blue truncate">
                {t.chatTitle}
              </h2>
              <p className="text-xs sm:text-sm text-turkey-red truncate">
                {t.chatSubtitle}
              </p>
            </div>
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6 bg-ghost-white">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full px-4">
                <div className="text-center max-w-md">
                  <Image
                    src="/logo.png"
                    alt={t.title}
                    width={100}
                    height={100}
                    className="mx-auto mb-4 sm:mb-6 rounded-xl sm:w-[120px] sm:h-[120px]"
                  />
                  <h3 className="text-xl sm:text-2xl font-bold text-oxford-blue mb-2 sm:mb-3">
                    {t.welcome}
                  </h3>
                  <p className="text-sm sm:text-base text-oxford-blue mb-4 sm:mb-6">
                    {t.welcomeText}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4 max-w-4xl mx-auto">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                  >
                    <div
                      className={`max-w-[85%] sm:max-w-2xl rounded-2xl px-4 py-3 sm:px-6 sm:py-4 ${message.role === 'user'
                          ? 'bg-fulvous text-white'
                          : 'bg-cornsilk text-oxford-blue border-2 border-fulvous'
                        }`}
                    >
                      {message.role === 'user' ? (
                        <p className="text-sm sm:text-base">{message.content}</p>
                      ) : (
                        <div className="prose prose-sm max-w-none">
                          {formatMessage(message.content)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="bg-cornsilk rounded-2xl px-4 py-4 sm:px-6 sm:py-5 border-2 border-fulvous">
                      <div className="flex items-center space-x-3">
                        <div className="relative">
                          <Image
                            src="/logo.png"
                            alt="Loading"
                            width={32}
                            height={32}
                            className="rounded-lg animate-pulse"
                          />
                          <div className="absolute inset-0 bg-fulvous rounded-lg animate-ping opacity-20"></div>
                        </div>
                        <div className="flex flex-col">
                          <p className="text-sm font-medium text-oxford-blue animate-fadeIn">
                            {loadingMessages[language][loadingMessage]}
                          </p>
                          <div className="flex items-center space-x-1 mt-2">
                            <div className="w-2 h-2 bg-fulvous rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-fulvous rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-fulvous rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}

            {error && (
              <div className="max-w-4xl mx-auto mt-4 animate-fadeIn">
                <div className="bg-turkey-red text-white rounded-lg p-3 sm:p-4">
                  <p className="font-semibold text-sm sm:text-base">{t.errorTitle}</p>
                  <p className="text-xs sm:text-sm mt-1">{error}</p>
                </div>
              </div>
            )}
          </div>

          {/* Input Area - Fixed at bottom on mobile */}
          <footer className="bg-white border-t-2 border-cornsilk p-3 sm:p-4 safe-bottom">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
              <div className="flex gap-2 sm:gap-3">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t.placeholder}
                  className="flex-1 px-4 py-3 sm:px-6 sm:py-3 border-2 border-fulvous rounded-full focus:outline-none focus:border-turkey-red text-oxford-blue text-sm sm:text-base transition-all"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="bg-turkey-red hover:bg-fulvous text-white px-6 py-3 sm:px-8 sm:py-3 rounded-full font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm sm:text-base active:scale-95 min-w-[80px] sm:min-w-[100px]"
                >
                  {loading ? t.searching : t.askButton}
                </button>
              </div>
            </form>
          </footer>
        </main>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </>
  );
}