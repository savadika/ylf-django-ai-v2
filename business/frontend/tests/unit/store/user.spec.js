import userModule from '@/store/modules/user'
import {
  getInfo,
  login,
  logout
} from '@/api/user'
import {
  removeToken,
  setToken
} from '@/utils/auth'
import { resetRouter } from '@/router'

jest.mock('@/api/user', () => ({
  getInfo: jest.fn(),
  getUserList: jest.fn(),
  login: jest.fn(),
  logout: jest.fn()
}))
jest.mock('@/utils/auth', () => ({
  getToken: jest.fn(() => ''),
  removeToken: jest.fn(),
  setToken: jest.fn()
}))
jest.mock('@/router', () => ({
  resetRouter: jest.fn()
}))

describe('user store', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    userModule.mutations.RESET_STATE(userModule.state)
  })

  it('logs in and persists the returned token', async () => {
    login.mockResolvedValue({ data: { token: 'new-token' } })
    const commit = jest.fn()

    await userModule.actions.login(
      { commit },
      { username: ' alice ', password: 'secret' }
    )

    expect(login).toHaveBeenCalledWith({
      username: 'alice',
      password: 'secret'
    })
    expect(commit).toHaveBeenCalledWith('SET_TOKEN', 'new-token')
    expect(setToken).toHaveBeenCalledWith('new-token')
  })

  it('loads profile data and generates menu routes', async () => {
    getInfo.mockResolvedValue({
      data: {
        id: 7,
        username: 'alice',
        avatar: 'uploads/alice.png',
        menus: [],
        permissions: ['system:user:list']
      }
    })
    const commit = jest.fn()
    const dispatch = jest.fn().mockResolvedValue([])

    await userModule.actions.getInfo({
      commit,
      dispatch,
      state: userModule.state
    })

    expect(commit).toHaveBeenCalledWith('SET_ID', 7)
    expect(commit).toHaveBeenCalledWith('SET_NAME', 'alice')
    expect(commit).toHaveBeenCalledWith(
      'SET_PERMISSIONS',
      ['system:user:list']
    )
    expect(dispatch).toHaveBeenCalledWith(
      'permission/generateRoutes',
      [],
      { root: true }
    )
  })

  it('clears local login state even if logout API fails', async () => {
    logout.mockRejectedValue(new Error('network'));
    const commit = jest.fn()

    await userModule.actions.logout({
      commit,
      state: { token: 'stale-token' }
    })

    expect(removeToken).toHaveBeenCalled()
    expect(resetRouter).toHaveBeenCalled()
    expect(commit).toHaveBeenCalledWith('RESET_STATE')
  })
})
