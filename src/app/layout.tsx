import type { Metadata } from "next";
import "./globals.css";
import ErrorReporter from "@/components/ErrorReporter";
import Script from "next/script";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/components/theme-provider";

export const metadata: Metadata = {
  title: "RepoRoverAI - AI-Powered Code Learning Platform",
  description: "Learn to code with AI-powered explanations, interactive lessons, and gamified learning paths",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <ErrorReporter />
          <Script
            src="https://slelguoygbfzlpylpxfs.supabase.co/storage/v1/object/public/scripts//route-messenger.js"
            strategy="afterInteractive"
            data-target-origin="*"
            data-message-type="ROUTE_CHANGE"
            data-include-search-params="true"
            data-only-in-iframe="true"
            data-debug="true"
            data-custom-data='{"appName": "YourApp", "version": "1.0.0", "greeting": "hi"}'
          />
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}