'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-16 flex-col bg-gray-900">
      <div className="flex flex-1 flex-col">
        <nav className="flex-1 space-y-1 px-2 py-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'group flex h-12 w-12 items-center justify-center rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                )}
                title={item.name}
              >
                <item.icon className="h-6 w-6" />
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
