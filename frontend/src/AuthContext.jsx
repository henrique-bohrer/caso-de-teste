import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('jwt_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get('/api/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch current user', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const loginWithCredentials = async (email, password) => {
    const response = await axios.post('/api/auth/login', { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('jwt_token', access_token);
    setToken(access_token);
    setUser(userData);
    return response.data;
  };

  const loginWithGoogle = async (credentialToken) => {
    const response = await axios.post('/api/auth/google', {
      credential_token: credentialToken
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('jwt_token', access_token);
    setToken(access_token);
    setUser(userData);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('jwt_token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, loginWithCredentials, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
