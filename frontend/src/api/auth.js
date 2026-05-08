import client from './client'

export const loginAPI    = (email, password)  => client.post('/auth/login', { email, password })
export const signupAPI   = (data)             => client.post('/auth/signup', data)
export const getMeAPI    = ()                 => client.get('/auth/me')
export const updateProfile = (updates)        => client.patch('/auth/profile', updates)
