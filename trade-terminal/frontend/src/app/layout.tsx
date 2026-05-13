"use client";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>Trade Terminal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="flex h-screen overflow-hidden bg-bg-primary">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <Topbar />
          <main className="flex-1 overflow-auto p-4">{children}</main>
        </div>
      </body>
    </html>
  );
}
