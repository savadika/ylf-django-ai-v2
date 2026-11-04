import request from '@/utils/request'
import { getCockpitSnapshot } from '@/api/cockpit'

jest.mock('@/utils/request', () => jest.fn())

describe('cockpit API', () => {
  it('loads the authenticated snapshot endpoint', () => {
    getCockpitSnapshot()

    expect(request).toHaveBeenCalledWith({
      url: '/cockpit/snapshot',
      method: 'get'
    })
  })
})
