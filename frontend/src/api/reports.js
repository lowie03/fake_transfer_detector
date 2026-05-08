import client from './client'

export const getStats  = ()                       => client.get('/reports/stats')
export const getLog    = (page = 1, limit = 10)   => client.get(`/reports/log?page=${page}&limit=${limit}`)
export const exportCSV = ()                       => client.get('/reports/export', { responseType: 'blob' })
export const getModelInfo = ()                    => client.get('/reports/model-info')
