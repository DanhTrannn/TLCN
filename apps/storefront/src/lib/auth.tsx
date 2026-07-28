"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ApiError, getMe, login as apiLogin, logout as apiLogout, register as apiRegister, type Customer } from "./api";

interface AuthContextValue {
  customer: Customer | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await getMe();
      setCustomer(me);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setCustomer(null);
      } else {
        setCustomer(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const me = await apiLogin({ email, password });
    setCustomer(me);
  }, []);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const me = await apiRegister({ email, password, display_name: displayName });
    setCustomer(me);
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setCustomer(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ customer, loading, login, register, logout, refresh }),
    [customer, loading, login, register, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
