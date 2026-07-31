export const dynamic = "force-dynamic";

export default async function Login({
  searchParams,
}: {
  searchParams: Promise<{ e?: string }>;
}) {
  const sp = await searchParams;
  return (
    <div className="loginwrap">
      <form className="logincard" method="post" action="/api/login">
        <h1>휴맥스 Cash Forecast</h1>
        <p className="sub">경영진 대시보드 · 비밀번호 입력</p>
        <input type="password" name="password" placeholder="비밀번호" autoFocus autoComplete="current-password" />
        <button type="submit">로그인</button>
        {sp?.e && <div className="loginerr">비밀번호가 올바르지 않습니다.</div>}
      </form>
    </div>
  );
}
