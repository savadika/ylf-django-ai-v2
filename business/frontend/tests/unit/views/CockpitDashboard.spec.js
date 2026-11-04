import { shallowMount } from '@vue/test-utils'
import EngineeringCockpit from '@/components/EngineeringCockpit/index.vue'
import { getCockpitSnapshot } from '@/api/cockpit'

jest.mock('@/api/cockpit', () => ({
  getCockpitSnapshot: jest.fn()
}))

const flushPromises = () => new Promise(resolve => setImmediate(resolve))

function createWrapper() {
  return shallowMount(EngineeringCockpit, {
    stubs: {
      'el-alert': true,
      'el-button': true
    }
  })
}

describe('engineering cockpit dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the authenticated cockpit snapshot in a sandboxed frame ac_001', async () => {
    getCockpitSnapshot.mockResolvedValue({
      data: {
        html: '<html><body class="embedded">驾驶舱</body></html>'
      }
    })

    const wrapper = createWrapper()
    await flushPromises()

    const frame = wrapper.find('iframe')
    expect(frame.exists()).toBe(true)
    expect(frame.attributes('sandbox')).toBe('')
    expect(frame.attributes('srcdoc')).toContain('驾驶舱')
    expect(wrapper.text()).not.toContain('订单数')
  })

  it('shows a retryable error when the snapshot request fails ac_001', async () => {
    getCockpitSnapshot.mockRejectedValue(new Error('network down'))

    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.vm.errorMessage).toBe('network down')
    expect(wrapper.find('iframe').exists()).toBe(false)
  })
})
