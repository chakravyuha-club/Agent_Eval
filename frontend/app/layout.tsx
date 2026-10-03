import './globals.css';
import { AuthProvider } from '@/lib/auth-context';

export const metadata = {
  title: 'AgentScore — AI Agent Evaluation Platform',
  description: 'Multi-Dimensional AI Agent Evaluation & Competition Platform for 18-Hour Hackathons',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#faf8ff] text-[#1e152a] antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
