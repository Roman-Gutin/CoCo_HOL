import { Routes, Route, Link, useLocation } from "react-router-dom";
import Overview from "./pages/Overview";
import AccountDetail from "./pages/AccountDetail";
import Chat from "./components/Chat";

function ChatWithContext() {
  const location = useLocation();
  const match = location.pathname.match(/^\/account\/(.+)/);
  const accountName = match?.[1] ? decodeURIComponent(match[1]) : undefined;
  return <Chat accountContext={accountName} />;
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Top navigation */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-30">
        <div className="mx-auto max-w-7xl flex items-center justify-between px-6 py-3">
          <Link to="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <span className="text-indigo-400">DNC</span>
            <span className="text-gray-400 font-normal text-sm hidden sm:inline">
              Account Health Dashboard
            </span>
          </Link>
        </div>
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/account/:id" element={<AccountDetail />} />
        </Routes>
      </main>

      {/* Floating chat panel — aware of current account context */}
      <ChatWithContext />
    </div>
  );
}
