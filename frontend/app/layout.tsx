import type { Metadata } from "next";
import "@fontsource/space-grotesk/700.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/fira-code/500.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Proposal Intel — Win More Bids",
  description: "AI-powered job discovery and proposal generation for freelancers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
