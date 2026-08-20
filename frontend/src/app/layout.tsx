import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MOSAIC | Personal Browser Agent",
  description: "MOSAIC learns the web, not your identity. A universal personal browser agent.",
};

import CursorGlow from "@/components/CursorGlow";
import { ThemeProvider } from "@/components/ThemeProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} h-full antialiased scroll-smooth`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-gradient-to-br from-[#fefce8] via-[#e0f2fe] to-[#ffffff] dark:from-[#050511] dark:via-[#1a0b2e] dark:to-[#051121] animate-gradient-xy text-slate-900 dark:text-slate-100 font-sans selection:bg-indigo-500/30">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <CursorGlow />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
