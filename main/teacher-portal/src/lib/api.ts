import { sm2 } from 'sm-crypto';

const BACKEND_URL = '/backend';

let pubConfigCache: { sm2PublicKey?: string } | null = null;

export async function getPubConfig(): Promise<{ sm2PublicKey?: string }> {
  if (pubConfigCache) return pubConfigCache;
  const res = await fetch(`${BACKEND_URL}/user/pub-config`);
  const json = await res.json();
  const data = json.code === 0 ? json.data : json;
  pubConfigCache = data;
  return data;
}

export function sm2Encrypt(publicKey: string, plainText: string): string {
  const encrypted = sm2.doEncrypt(plainText, publicKey, 1);
  return '04' + encrypted;
}

export async function encryptPassword(password: string, captchaText?: string): Promise<string> {
  const config = await getPubConfig();
  if (config.sm2PublicKey) {
    const plain = captchaText ? captchaText + password : password;
    return sm2Encrypt(config.sm2PublicKey, plain);
  }
  return password;
}

export async function backendFetch(
  path: string,
  options: RequestInit & { token?: string } = {}
) {
  const { token, headers: customHeaders, ...rest } = options;
  const headers: Record<string, string> = {
    ...(customHeaders as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(rest.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  const res = await fetch(`${BACKEND_URL}${path}`, { ...rest, headers });

  if (!res.ok && res.status >= 500) {
    throw new Error('Server đang khởi động hoặc gặp sự cố. Vui lòng thử lại.');
  }

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error('Không thể kết nối đến hệ thống. Vui lòng kiểm tra Manager API đã khởi động chưa.');
  }

  if (data.code !== undefined && data.code === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      const locale = window.location.pathname.split('/')[1];
      const prefix = ['vi', 'en'].includes(locale) ? `/${locale}` : '';
      window.location.href = `${prefix}/login`;
    }
    throw new Error('Phiên đăng nhập hết hạn');
  }

  if (data.code !== undefined && data.code !== 0) {
    throw new Error(data.msg || 'Có lỗi từ server');
  }
  return data.data !== undefined ? data.data : data;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('teacher_token');
}

export function setToken(token: string) {
  localStorage.setItem('teacher_token', token);
}

export function clearToken() {
  localStorage.removeItem('teacher_token');
  localStorage.removeItem('teacher_user');
}

export function getUser(): { username: string; id?: string } | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem('teacher_user');
  return raw ? JSON.parse(raw) : null;
}

export function setUser(user: { username: string; id?: string }) {
  localStorage.setItem('teacher_user', JSON.stringify(user));
}
