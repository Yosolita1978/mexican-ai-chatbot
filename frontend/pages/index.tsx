import { useState, useEffect } from 'react';
import Head from 'next/head';
import Image from 'next/image';
import { searchRecipes } from '@/lib/api';
import { translations, detectLanguage, Language } from '@/lib/translations';

export default function Home() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<Language>('en');

  useEffect(() => {
    setLanguage(detectLanguage());
  }, []);

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
      const response = await searchRecipes(userMessage);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    } catch (err) {
      console.error('Error searching recipes:', err);
      setError('Failed to connect to recipe service.');
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I couldn\'t search for recipes right now.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuery = (queryText: string) => {
    setQuery(queryText);
  };

  const formatMessage = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, index) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        const text = line.replace(/\*\*/g, '');
        return <h3 key={index} className="text-lg font-bold text-turkey-red mt-4 mb-2">{text}</h3>;
      }
      if (line.startsWith('*') && line.endsWith('*')) {
        const text = line.replace(/\*/g, '');
        return <p key={index} className="text-sm text-oxford-blue opacity-75 mb-2">{text}</p>;
      }
      if (line === '---') {
        return <hr key={index} className="my-4 border-fulvous" />;
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index} className="mb-2">{line}</p>;
    });
  };

  return (
    <>
      <Head>
        <title>{t.title} - {t.subtitle}</title>
        <meta name="description" content="Authentic Mexican recipes from the Benítez family" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/logo.png" />
      </Head>

      <div className="flex h-screen bg-ghost-white">
        {/* Sidebar */}
        <aside className="w-80 bg-oxford-blue text-cornsilk flex flex-col border-r-4 border-fulvous">
          {/* Logo Header */}
          <div className="p-6 border-b-2 border-fulvous">
            <div className="flex items-center gap-3 mb-4">
              <Image 
                src="/logo.png" 
                alt={t.title}
                width={60} 
                height={60}
                className="rounded-lg"
              />
              <div>
                <h1 className="text-xl font-bold">{t.title}</h1>
                <p className="text-xs text-fulvous">{t.subtitle}</p>
              </div>
            </div>
            
            {/* Language Toggle */}
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setLanguage('en')}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-semibold transition-colors ${
                  language === 'en' 
                    ? 'bg-fulvous text-white' 
                    : 'bg-oxford-blue text-cornsilk border border-fulvous hover:bg-turkey-red'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('es')}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-semibold transition-colors ${
                  language === 'es' 
                    ? 'bg-fulvous text-white' 
                    : 'bg-oxford-blue text-cornsilk border border-fulvous hover:bg-turkey-red'
                }`}
              >
                Español
              </button>
            </div>
          </div>

          {/* Quick Search Buttons */}
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-sm font-bold text-fulvous mb-4 uppercase tracking-wide">
              {t.quickRecipes}
            </h2>
            <div className="space-y-3">
              <button
                onClick={() => handleQuickQuery(t.queryPozole)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.pozole}</div>
                <div className="text-xs text-cornsilk mt-1">{t.pozoleDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.queryChicken)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.chicken}</div>
                <div className="text-xs text-cornsilk mt-1">{t.chickenDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.querySoups)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.soups}</div>
                <div className="text-xs text-cornsilk mt-1">{t.soupsDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.queryFajitas)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.fajitas}</div>
                <div className="text-xs text-cornsilk mt-1">{t.fajitasDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.queryPasta)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.pasta}</div>
                <div className="text-xs text-cornsilk mt-1">{t.pastaDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.queryDesserts)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.desserts}</div>
                <div className="text-xs text-cornsilk mt-1">{t.dessertsDesc}</div>
              </button>

              <button
                onClick={() => handleQuickQuery(t.querySeafood)}
                className="w-full text-left p-4 bg-turkey-red hover:bg-fulvous rounded-lg transition-colors"
              >
                <div className="font-bold text-white">{t.seafood}</div>
                <div className="text-xs text-cornsilk mt-1">{t.seafoodDesc}</div>
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t-2 border-fulvous">
            <p className="text-xs text-cornsilk text-center">
              {t.footerText}
            </p>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col">
          {/* Chat Header */}
          <header className="bg-white border-b-2 border-cornsilk p-4 shadow-sm">
            <h2 className="text-xl font-bold text-oxford-blue">
              {t.chatTitle}
            </h2>
            <p className="text-sm text-turkey-red">
              {t.chatSubtitle}
            </p>
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 bg-ghost-white">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md">
                  <Image 
                    src="/logo.png" 
                    alt={t.title}
                    width={120} 
                    height={120}
                    className="mx-auto mb-6 rounded-xl"
                  />
                  <h3 className="text-2xl font-bold text-oxford-blue mb-3">
                    {t.welcome}
                  </h3>
                  <p className="text-oxford-blue mb-6">
                    {t.welcomeText}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4 max-w-4xl mx-auto">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-2xl rounded-2xl px-6 py-4 ${
                        message.role === 'user'
                          ? 'bg-fulvous text-white'
                          : 'bg-cornsilk text-oxford-blue border-2 border-fulvous'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <p>{message.content}</p>
                      ) : (
                        <div className="prose prose-sm max-w-none">
                          {formatMessage(message.content)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-cornsilk rounded-2xl px-6 py-4 border-2 border-fulvous">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-fulvous rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-fulvous rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-fulvous rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {error && (
              <div className="max-w-4xl mx-auto mt-4">
                <div className="bg-turkey-red text-white rounded-lg p-4">
                  <p className="font-semibold">{t.errorTitle}</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <footer className="bg-white border-t-2 border-cornsilk p-4">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t.placeholder}
                  className="flex-1 px-6 py-3 border-2 border-fulvous rounded-full focus:outline-none focus:border-turkey-red text-oxford-blue"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="bg-turkey-red hover:bg-fulvous text-white px-8 py-3 rounded-full font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? t.searching : t.askButton}
                </button>
              </div>
            </form>
          </footer>
        </main>
      </div>
    </>
  );
}