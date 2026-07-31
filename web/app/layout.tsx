import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "휴맥스 Cash Forecast 대시보드",
  description: "주간 현금흐름 경영진 대시보드",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
