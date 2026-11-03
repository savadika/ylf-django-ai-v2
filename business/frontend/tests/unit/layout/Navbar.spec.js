import { shallowMount } from '@vue/test-utils'
import Navbar from '@/layout/components/Navbar.vue'
import { updateProfile } from '@/api/user'

jest.mock('@/api/user', () => ({
  updateProfile: jest.fn()
}))
jest.mock('@/api/upload', () => ({
  uploadFile: jest.fn()
}))

const flushPromises = () => new Promise(resolve => setImmediate(resolve))

function createWrapper() {
  const dispatch = jest.fn().mockResolvedValue()
  const replace = jest.fn()
  const wrapper = shallowMount(Navbar, {
    mocks: {
      $route: { fullPath: '/dashboard' },
      $router: { replace },
      $store: {
        commit: jest.fn(),
        dispatch,
        getters: {
          avatar: 'old-avatar.png',
          id: 9,
          name: 'alice',
          sidebar: { opened: true }
        }
      },
      $message: {
        error: jest.fn(),
        success: jest.fn()
      }
    },
    stubs: [
      'breadcrumb',
      'el-dropdown',
      'el-dropdown-item',
      'el-dropdown-menu',
      'el-dialog',
      'el-form',
      'el-form-item',
      'el-input',
      'el-button',
      'el-upload',
      'hamburger'
    ]
  })
  wrapper.vm.$refs.profileForm = {
    clearValidate: jest.fn(),
    validate: callback => callback(true)
  }
  return { wrapper, dispatch, replace }
}

describe('Navbar personal profile', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('updates the current user through the dedicated profile API', async () => {
    updateProfile.mockResolvedValue({
      data: {
        avatar: 'uploads/new-avatar.png',
        reauth_required: false
      }
    })
    const { wrapper } = createWrapper()
    wrapper.setData({
      profileForm: {
        avatar: 'uploads/new-avatar.png',
        confirmPassword: '',
        password: ''
      }
    })

    wrapper.vm.updateProfile()
    await flushPromises()

    expect(updateProfile).toHaveBeenCalledWith({
      avatar: 'uploads/new-avatar.png'
    })
    expect(wrapper.vm.$store.commit).toHaveBeenCalledWith(
      'user/SET_AVATAR',
      'uploads/new-avatar.png'
    )
  })

  it('clears the local session after a password change', async () => {
    updateProfile.mockResolvedValue({
      data: {
        avatar: 'old-avatar.png',
        reauth_required: true
      }
    })
    const { wrapper, dispatch, replace } = createWrapper()
    wrapper.setData({
      profileForm: {
        avatar: 'old-avatar.png',
        confirmPassword: 'StrongPass456!',
        password: 'StrongPass456!'
      }
    })

    wrapper.vm.updateProfile()
    await flushPromises()

    expect(dispatch).toHaveBeenCalledWith('user/resetToken')
    expect(replace).toHaveBeenCalledWith(
      '/login?redirect=%2Fdashboard'
    )
  })
})
