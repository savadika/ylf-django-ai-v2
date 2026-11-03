import permission, {
  normalizeComponentPath,
  transformMenusToRoutes
} from '@/store/modules/permission'

jest.mock('@/router', () => ({
  constantRoutes: []
}))
jest.mock('@/layout', () => ({
  __esModule: true,
  default: { name: 'Layout' }
}))
jest.mock('@/layout/components/EmptyLayout', () => ({
  __esModule: true,
  default: { name: 'EmptyLayout' }
}))

describe('dynamic permission routes', () => {
  it('normalizes supported legacy component paths', () => {
    expect(normalizeComponentPath('views/system/user/index.vue')).toBe('user/index')
    expect(normalizeComponentPath('/system/role/index.vue')).toBe('role/index')
  })

  it('builds nested page routes and skips button permissions', () => {
    const routes = transformMenusToRoutes([
      {
        name: '系统管理',
        path: '/system',
        menu_type: 'M',
        children: [
          {
            name: '用户管理',
            path: '/system/user',
            component: 'user/index',
            menu_type: 'C'
          },
          {
            name: '删除用户',
            menu_type: 'F',
            perms: 'system:user:delete'
          }
        ]
      }
    ])

    expect(routes).toHaveLength(1)
    expect(routes[0].children).toHaveLength(1)
    expect(routes[0].children[0].path).toBe('user')
    expect(routes[0].children[0].meta.title).toBe('用户管理')
  })

  it('stores generated routes and resets generated state', async () => {
    const commit = jest.fn()
    await permission.actions.generateRoutes({ commit }, [])

    expect(commit).toHaveBeenCalledWith('SET_ROUTES', [])
    permission.mutations.RESET_ROUTES(permission.state)
    expect(permission.state.generated).toBe(false)
    expect(permission.state.addRoutes).toEqual([])
  })
})
