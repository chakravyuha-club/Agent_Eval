'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import {
  LayoutDashboard, FileText, Database, UploadCloud,
  CheckCircle2, Trophy, Users, Sliders, ShieldCheck,
  History, LogOut
} from 'lucide-react';
import ThemeToggle from '@/components/ThemeToggle';

interface SidebarProps {
  isAdmin?: boolean;
}

export default function Sidebar({ isAdmin = false }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const teamNavItems = [
    { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Problem Statement', href: '/dashboard/problem', icon: FileText },
    { name: 'Datasets', href: '/dashboard/datasets', icon: Database },
    { name: 'Submissions', href: '/dashboard/submissions', icon: UploadCloud },
    { name: 'Evaluation Results', href: '/dashboard/results', icon: CheckCircle2 },
    { name: 'Leaderboard', href: '/dashboard/leaderboard', icon: Trophy },
  ];

  const adminNavItems = [
    { name: 'Admin Overview', href: '/admin', icon: LayoutDashboard },
    { name: 'Team Management', href: '/admin/teams', icon: Users },
    { name: 'Evaluation Queue', href: '/admin/evaluations', icon: History },
    { name: 'Scoring Rubrics', href: '/admin/rubrics', icon: Sliders },
    { name: 'Competition Controls', href: '/admin/controls', icon: ShieldCheck },
    { name: 'Audit Logs', href: '/admin/audit-logs', icon: FileText },
  ];

  const navItems = isAdmin ? adminNavItems : teamNavItems;

  return (
    <aside className="w-64 bg-white dark:bg-[#0e091d]/90 border-r border-purple-100 dark:border-purple-900/30 flex flex-col justify-between h-[calc(100vh-4rem)] sticky top-16 shadow-sm transition-colors duration-300">
      <div className="p-4 space-y-6">
        <div className="px-3.5 py-2.5 bg-purple-50/70 dark:bg-purple-950/40 rounded-2xl border border-purple-100 dark:border-purple-800/40">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-purple-600 dark:text-purple-400">
            {isAdmin ? 'Administrative Suite' : 'Team Workspace'}
          </p>
          <p className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate mt-0.5">
            {isAdmin ? (user?.email || 'Super Admin') : (user?.team_name || user?.team_code?.toUpperCase() || 'Participant')}
          </p>
          {!isAdmin && user?.team_code && (
            <span className="inline-block px-2 py-0.5 mt-1.5 text-[11px] font-semibold bg-purple-200/80 dark:bg-purple-900/80 text-purple-900 dark:text-purple-200 rounded-md">
              ID: {user.team_code}
            </span>
          )}
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/30 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:text-purple-700 dark:hover:text-purple-300 hover:bg-purple-50/70 dark:hover:bg-purple-950/40'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400 dark:text-slate-500'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-purple-50 dark:border-purple-900/20 space-y-2">
        <div className="flex items-center justify-between px-2 py-1">
          <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Theme</span>
          <ThemeToggle />
        </div>
        <button
          onClick={logout}
          className="flex items-center space-x-2 w-full px-3 py-2 text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-xl transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
