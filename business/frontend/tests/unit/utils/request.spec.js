import request from '@/utils/request'
import { Message } from 'element-ui'
import { getToken } from '@/utils/auth'
import store from '@/store'

jest.mock('element-ui', () => ({
  Message: jest.fn(),
  MessageBox: {
    confirm: jest.fn()
  }
}))
jest.mock('@/store', () => ({
  __esModule: true,
  default: {
    dispatch: jest.fn(),
    getters: { token: 'store-token' }
  }
}))
jest.mock('@/utils/auth', () => ({
  getToken: jest.fn(() => 'raw-token')
}))
jest.mock('@/utils/config', () => ({
  getBaseApiUrl: () => 'http://backend.test'
}))

describe('request interceptors', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('adds the current token without a prefix', () => {
    const handler = request.interceptors.request.handlers[0].fulfilled
    const config = handler({ headers: {} })

    expect(store.getters.token).toBe('store-token')
    expect(getToken).toHaveBeenCalled()
    expect(config.headers.Authorization).toBe('raw-token')
  })

  it('returns successful response envelopes unchanged', () => {
    const handler = request.interceptors.response.handlers[0].fulfilled
    const response = {
      data: {
        code: 200,
        message: 'ok',
        data: { id: 1 }
      }
    }

    expect(handler(response)).toBe(response.data)
  })

  it('shows a deduplicated warning for forbidden responses', async () => {
    const rejected = request.interceptors.response.handlers[0].rejected

    await expect(
      rejected({ response: { status: 403, data: { message: 'forbidden' } } })
    ).rejects.toBeTruthy()
    expect(Message).toHaveBeenCalledWith(
      expect.objectContaining({
        message: '无权限访问该资源',
        type: 'warning'
      })
    )
  })
})
