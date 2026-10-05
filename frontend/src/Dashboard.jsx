import React from 'react';
import { useAuth } from './AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Área Protegida</h1>
        <p style={styles.welcome}>
          Bem-vindo, <strong>{user?.name || user?.email}</strong>!
        </p>
        <div style={styles.infoGroup}>
          <p><strong>ID do Usuário:</strong> {user?.id}</p>
          <p><strong>E-mail:</strong> {user?.email}</p>
        </div>

        <button onClick={handleLogout} style={styles.logoutBtn}>
          Sair
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f3f4f6',
    fontFamily: 'sans-serif'
  },
  card: {
    backgroundColor: '#ffffff',
    padding: '2.5rem',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    width: '100%',
    maxWidth: '450px',
    textAlign: 'center'
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: '1rem'
  },
  welcome: {
    fontSize: '1.125rem',
    color: '#374151',
    marginBottom: '1.5rem'
  },
  infoGroup: {
    backgroundColor: '#f9fafb',
    padding: '1rem',
    borderRadius: '8px',
    textAlign: 'left',
    marginBottom: '1.5rem',
    color: '#4b5563'
  },
  logoutBtn: {
    backgroundColor: '#ef4444',
    color: '#ffffff',
    fontWeight: '600',
    padding: '0.625rem 1.25rem',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer'
  }
};
