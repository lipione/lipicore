import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import TopBar from '../components/layout/TopBar';
import SecureMessengerWidget from '../components/messenger/SecureMessengerWidget';

export default function MainLayout() {
  const [language, setLanguage] = useState(
    () => localStorage.getItem('language') || 'en'
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    localStorage.setItem('language', lang);
  };

  const handleUpload = () => {
    navigate('/documents');
  };

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-slate-950/30 z-30 lg:hidden"
        />
      )}
      <Sidebar onUpload={handleUpload} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-col flex-1 lg:ml-64 min-w-0">
        <TopBar
          language={language}
          onLanguageChange={handleLanguageChange}
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main className="flex-1 overflow-auto mt-16">
          <Outlet context={{ language, setLanguage: handleLanguageChange }} />
        </main>
        <SecureMessengerWidget />
      </div>
    </div>
  );
}
