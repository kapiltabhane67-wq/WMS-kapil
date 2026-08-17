import { API_BASE } from "./constants";
import type { User } from "./types";

type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
};

async function parseError(response: Response) {
  const body = await response.text();
  if (!body) return response.statusText;
  try {
    const parsed = JSON.parse(body);
    return parsed.detail ?? parsed.message ?? body;
  } catch {
    return body;
  }
}

async function requestJson<T>(path: string, options: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    return response.json();
  } catch (caught) {
    if (caught instanceof TypeError) {
      throw new Error("Unable to reach the WMS backend. Check the deployed API URL and CORS settings.");
    }
    throw caught;
  }
}

export async function api<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  return requestJson<T>(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
  });
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return requestJson<LoginResponse>("/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function uploadFile<T>(path: string, token: string, formData: FormData): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });
}
