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
    <aside className="w-64 bg-white border-r border-purple-100 flex flex-col justify-between h-[calc(100vh-4rem)] sticky top-16 shadow-sm">
      <div className="p-4 space-y-6">
        <div className="px-3 py-2 bg-purple-50/70 rounded-xl border border-purple-100">
          <p className="text-xs font-semibold uppercase tracking-wider text-purple-600">
            {isAdmin ? 'Administrative Suite' : 'Team Workspace'}
          </p>
          <p className="text-sm font-bold text-slate-800 truncate mt-0.5">
            {isAdmin ? (user?.email || 'Super Admin') : (user?.team_name || user?.team_code?.toUpperCase() || 'Participant')}
          </p>
          {!isAdmin && user?.team_code && (
            <span className="inline-block px-2 py-0.5 mt-1.5 text-[11px] font-semibold bg-purple-200/80 text-purple-900 rounded-md">
              ID: {user.team_code}
            </span>
          )}
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/20'
                    : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-purple-50">
        <button
          onClick={logout}
          className="flex items-center space-x-2 w-full px-3 py-2 text-sm font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
