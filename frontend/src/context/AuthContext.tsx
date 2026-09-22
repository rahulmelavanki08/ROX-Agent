import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";

export interface AuthUser {
  user_id: string;
  email: string;
  authenticated_at: number;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  requestOtp: (email: string) => Promise<any>;
  verifyOtp: (email: string, otp: string) => Promise<any>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem("rox_auth_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem("rox_auth_token");
  });
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  useEffect(() => {
    if (token) {
      api.getMe(token).then((data) => {
        if (data && data.authenticated && data.user) {
          setUser(data.user);
          localStorage.setItem("rox_auth_user", JSON.stringify(data.user));
        } else {
          // Token expired or invalid
          setUser(null);
          setToken(null);
          localStorage.removeItem("rox_auth_token");
          localStorage.removeItem("rox_auth_user");
        }
      }).catch(() => {
        // Network or offline, retain cached user
      });
    }
  }, [token]);

  const requestOtp = async (email: string) => {
    return await api.requestOtp(email);
  };

  const verifyOtp = async (email: string, otp: string) => {
    const res = await api.verifyOtp(email, otp);
    if (res && res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      localStorage.setItem("rox_auth_token", res.token);
      localStorage.setItem("rox_auth_user", JSON.stringify(res.user));
      setIsAuthModalOpen(false);
    }
    return res;
  };

  const logout = async () => {
    if (token) {
      try {
        await api.logout(token);
      } catch (e) {}
    }
    setUser(null);
    setToken(null);
    localStorage.removeItem("rox_auth_token");
    localStorage.removeItem("rox_auth_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(user && token),
        isAuthModalOpen,
        openAuthModal: () => setIsAuthModalOpen(true),
        closeAuthModal: () => setIsAuthModalOpen(false),
        requestOtp,
        verifyOtp,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
