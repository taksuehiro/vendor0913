const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Vendor {
  id: number;
  name: string;
  category: string;
  description?: string;
  website_url?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  name: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface SearchRequest {
  query: string;
  max_results?: number;
}

export interface SearchResult {
  vendor_name: string;
  category: string;
  description: string;
  score: number;
  website_url?: string;
}

// APIクライアントクラス
export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    if (this.token) {
      (headers as Record<string, string>).Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // 認証関連
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'ログインに失敗しました');
    }

    return response.json();
  }

  async register(userData: RegisterRequest): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // ベンダー関連
  async getVendors(): Promise<Vendor[]> {
    return this.request<Vendor[]>('/vendors');
  }

  async createVendor(vendorData: Omit<Vendor, 'id' | 'created_at' | 'updated_at'>): Promise<Vendor> {
    return this.request<Vendor>('/vendors', {
      method: 'POST',
      body: JSON.stringify(vendorData),
    });
  }

  // 検索機能
  async searchVendors(searchRequest: SearchRequest): Promise<SearchResult[]> {
    return this.request<SearchResult[]>('/search/vendors', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }
}

// シングルトンインスタンス
export const apiClient = new ApiClient();