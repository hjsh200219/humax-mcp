import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 비밀번호 게이트: 유효한 인증 쿠키가 없으면 /login 으로 보낸다.
// 쿠키에는 평문 비밀번호가 아니라 SHA-256 토큰을 저장한다.
async function expectedToken(): Promise<string> {
  const pw = process.env.DASHBOARD_PASSWORD ?? "";
  const data = new TextEncoder().encode(pw + "::humax-cf");
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (pathname.startsWith("/login") || pathname.startsWith("/api/login")) {
    return NextResponse.next();
  }
  const token = req.cookies.get("dash_auth")?.value;
  if (token && token === (await expectedToken())) {
    return NextResponse.next();
  }
  const url = req.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  return NextResponse.redirect(url);
}

// 정적 자산(_next)과 파비콘은 게이트 제외
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
