import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Knowledge Search',
  robots: { index: false, follow: false, noarchive: true },
};

export default function AppLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
