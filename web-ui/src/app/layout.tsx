import type { Metadata } from 'next';
import { Inter, Playfair_Display, JetBrains_Mono } from 'next/font/google';
import { ThemeProvider } from '@/components/providers/theme-provider';
import { QueryProvider } from '@/components/providers/query-provider';
import { AuthProvider } from '@/components/providers/auth-provider';
import { Toaster } from '@/components/ui/toaster';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-serif',
});

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: {
    default: 'Daemonium - Converse with Philosophers',
    template: '%s | Daemonium',
  },
  description: 'Engage in meaningful conversations with AI-powered philosopher personas. Explore wisdom from ancient to contemporary thinkers.',
  keywords: ['philosophy', 'AI', 'conversation', 'wisdom', 'learning', 'education'],
  authors: [{ name: 'Daemonium Team' }],
  creator: 'Daemonium',
  publisher: 'Daemonium',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://daemonium.app'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://daemonium.app',
    title: 'Daemonium - Converse with Philosophers',
    description: 'Engage in meaningful conversations with AI-powered philosopher personas.',
    siteName: 'Daemonium',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Daemonium - Converse with Philosophers',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Daemonium - Converse with Philosophers',
    description: 'Engage in meaningful conversations with AI-powered philosopher personas.',
    images: ['/og-image.jpg'],
    creator: '@daemonium',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'google-site-verification-code',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${playfair.variable} ${jetbrains.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <QueryProvider>
              <div className="relative flex min-h-screen flex-col">
                <div className="flex-1">{children}</div>
              </div>
              <Toaster />
            </QueryProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
