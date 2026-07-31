import { NextResponse } from "next/server";

async function token(pw: string): Promise<string> {
  const data = new TextEncoder().encode(pw + "::humax-cf");
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function POST(req: Request) {
  const form = await req.formData();
  const pw = String(form.get("password") ?? "");
  const expected = process.env.DASHBOARD_PASSWORD ?? "";

  if (pw && expected && pw === expected) {
    const res = NextResponse.redirect(new URL("/", req.url), 303);
    res.cookies.set("dash_auth", await token(pw), {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 12, // 12시간
    });
    return res;
  }
  return NextResponse.redirect(new URL("/login?e=1", req.url), 303);
}
