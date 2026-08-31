import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Neighborhood Library",
  description: "Manage books, members, and loans for the neighborhood library.",
};

const navLinks = [
  { href: "/books", label: "Books" },
  { href: "/members", label: "Members" },
  { href: "/loans", label: "Loans" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
            <Link href="/" className="font-semibold text-slate-900">
              📚 Neighborhood Library
            </Link>
            <nav className="flex gap-4 text-sm font-medium text-slate-600">
              {navLinks.map((link) => (
                <Link key={link.href} href={link.href} className="hover:text-slate-900">
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
