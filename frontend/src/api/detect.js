import client from './client'

export const detectScreenshot = (file, bank = 'unknown') => {
  const form = new FormData()
  form.append('file', file)
  form.append('bank', bank)
  return client.post('/detect/screenshot', form)
}

export const detectSMS = (text, bank = 'unknown') =>
  client.post('/detect/sms', { text, bank })
