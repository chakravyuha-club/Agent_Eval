import './globals.css';
import localFont from 'next/font/local';
import { AuthProvider } from '@/lib/auth-context';
import { ThemeProvider } from '@/lib/theme-context';
import CustomCursor from '@/components/CustomCursor';

const oxygen = localFont({
  src: [
    {
      path: './fonts/Oxygen-Light.ttf',
      weight: '300',
      style: 'normal',
    },
    {
      path: './fonts/Oxygen-Regular.ttf',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/Oxygen-Bold.ttf',
      weight: '700',
      style: 'normal',
    },
  ],
  variable: '--font-oxygen',
  display: 'swap',
});

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
    <html lang="en" className={`${oxygen.variable} font-sans`} suppressHydrationWarning>
      <body className="min-h-screen bg-[#faf8ff] text-[#1e152a] dark:bg-[#0a0714] dark:text-[#f3e8ff] antialiased transition-colors duration-300">
        <ThemeProvider>
          <AuthProvider>
            <CustomCursor />
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
