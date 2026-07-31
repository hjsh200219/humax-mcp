import "server-only";
import { createClient } from "@supabase/supabase-js";

// 서버 전용 클라이언트. service_role 키는 브라우저로 절대 전달되지 않는다
// (이 모듈은 server-only 로 표시되어 클라이언트 번들에 포함되면 빌드가 실패한다).
const url = process.env.SUPABASE_URL;
const key = process.env.SUPABASE_SERVICE_KEY;

if (!url || !key) {
  throw new Error("SUPABASE_URL / SUPABASE_SERVICE_KEY 환경변수가 필요합니다. web/.env.local 참조.");
}

export const supabase = createClient(url, key, {
  auth: { persistSession: false, autoRefreshToken: false },
});
