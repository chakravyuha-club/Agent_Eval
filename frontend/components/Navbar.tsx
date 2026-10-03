'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Shield, Trophy, LayoutDashboard, LogOut, LogIn } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-purple-100 bg-white/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-700 via-purple-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-purple-500/20">
                <Shield className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold tracking-tight text-purple-950">
                Agent<span className="text-purple-600">Score</span>
              </span>
            </Link>
          </div>

          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-600">
            <Link href="/" className="hover:text-purple-600 transition-colors">Home</Link>
            <Link href="/dashboard/problem" className="hover:text-purple-600 transition-colors">Problem & Datasets</Link>
            <Link href="/dashboard/leaderboard" className="flex items-center space-x-1 hover:text-purple-600 transition-colors">
              <Trophy className="w-4 h-4 text-purple-500" />
              <span>Leaderboard</span>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-3">
                <Link
                  href={user.role === 'admin' ? '/admin' : '/dashboard'}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors flex items-center space-x-1.5"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span>{user.role === 'admin' ? 'Admin Portal' : (user.team_code?.toUpperCase() || 'Dashboard')}</span>
                </Link>
                <button
                  onClick={logout}
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium rounded-lg bg-purple-600 text-white hover:bg-purple-700 shadow-sm shadow-purple-600/30 transition-all flex items-center space-x-1.5"
              >
                <LogIn className="w-4 h-4" />
                <span>Team Login</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
