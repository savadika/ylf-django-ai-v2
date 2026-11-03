import { getToken, removeToken, setToken } from '@/utils/auth'

describe('token storage', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  it('stores the token only in the current tab', () => {
    setToken('current-tab-token')

    expect(getToken()).toBe('current-tab-token')
    expect(sessionStorage.getItem('Authorization')).toBe('current-tab-token')
    expect(localStorage.getItem('Authorization')).toBeNull()
  })

  it('removes the current-tab token', () => {
    setToken('current-tab-token')
    removeToken()

    expect(getToken()).toBe('')
    expect(sessionStorage.getItem('Authorization')).toBeNull()
  })
})
