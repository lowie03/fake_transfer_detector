import React, { createContext, useContext, useState, useEffect } from 'react'
import { loginAPI, signupAPI } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedToken = localStorage.getItem('tg_token')
    const savedUser  = localStorage.getItem('tg_user')
    if (savedToken && savedUser) {
      try {
        setToken(savedToken)
        setUser(JSON.parse(savedUser))
      } catch {
        localStorage.removeItem('tg_token')
        localStorage.removeItem('tg_user')
      }
    }
    setLoading(false)
  }, [])

  const _persist = (tok, userData) => {
    localStorage.setItem('tg_token', tok)
    localStorage.setItem('tg_user', JSON.stringify(userData))
    setToken(tok)
    setUser(userData)
  }

  const login = async (email, password) => {
    const res = await loginAPI(email, password)
    _persist(res.data.token, res.data.user)
  }

  const signup = async (data) => {
    const res = await signupAPI(data)
    _persist(res.data.token, res.data.user)
  }

  const logout = () => {
    localStorage.removeItem('tg_token')
    localStorage.removeItem('tg_user')
    setToken(null)
    setUser(null)
  }

  const updateUser = (updates) => {
    const updated = { ...user, ...updates }
    localStorage.setItem('tg_user', JSON.stringify(updated))
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, loading, login, signup, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
