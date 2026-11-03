import request from '@/utils/request'
import * as userApi from '@/api/user'
import * as roleApi from '@/api/role'
import * as menuApi from '@/api/menu'
import * as departmentApi from '@/api/department'

jest.mock('@/utils/request', () => jest.fn())

// SPEC-006 AC-006: verify the public API adapter contract for each core resource.
describe('core resource API contracts', () => {
  beforeEach(() => {
    request.mockReset()
    request.mockResolvedValue({ code: 200, data: null })
  })

  describe('user API', () => {
    const payload = { username: 'tester', password: 'StrongPass123!' }
    const cases = [
      ['login', () => userApi.login(payload), { url: '/user/gen_token', method: 'post', data: payload }],
      ['getInfo', () => userApi.getInfo(), { url: '/user/get_user_info', method: 'get' }],
      ['logout', () => userApi.logout(), { url: '/user/logout', method: 'post' }],
      ['updateProfile', () => userApi.updateProfile({ avatar: 'uploads/me.png' }), { url: '/user/profile', method: 'patch', data: { avatar: 'uploads/me.png' } }],
      ['getUserList', () => userApi.getUserList({ page: 2 }), { url: '/user', method: 'get', params: { page: 2 } }],
      ['createUser', () => userApi.createUser(payload), { url: '/user', method: 'post', data: payload }],
      ['getUserDetail', () => userApi.getUserDetail(7), { url: '/user/7', method: 'get' }],
      ['updateUser', () => userApi.updateUser(7, payload), { url: '/user/7', method: 'put', data: payload }],
      ['patchUser', () => userApi.patchUser(7, { status: 0 }), { url: '/user/7', method: 'patch', data: { status: 0 } }],
      ['deleteUser', () => userApi.deleteUser(7), { url: '/user/7', method: 'delete' }]
    ]

    it.each(cases)('%s sends the expected request', (_name, invoke, expected) => {
      invoke()
      expect(request).toHaveBeenCalledWith(expected)
    })
  })

  describe('role API', () => {
    const payload = { name: '测试角色', code: 'test-role' }
    const cases = [
      ['getRoleList', () => roleApi.getRoleList({ page: 2 }), { url: '/role', method: 'get', params: { page: 2 } }],
      ['getRoleDetail', () => roleApi.getRoleDetail(3), { url: '/role/3', method: 'get' }],
      ['createRole', () => roleApi.createRole(payload), { url: '/role', method: 'post', data: payload }],
      ['updateRole', () => roleApi.updateRole(3, payload), { url: '/role/3', method: 'put', data: payload }],
      ['patchRole', () => roleApi.patchRole(3, { name: '新名称' }), { url: '/role/3', method: 'patch', data: { name: '新名称' } }],
      ['deleteRole', () => roleApi.deleteRole(3), { url: '/role/3', method: 'delete' }],
      ['updateRolePermissions', () => roleApi.updateRolePermissions(3, { permissions: [1, 2] }), { url: '/role/3/permissions', method: 'put', data: { permissions: [1, 2] } }],
      ['getRoleMenus', () => roleApi.getRoleMenus(3), { url: '/role/3/menus', method: 'get' }]
    ]

    it.each(cases)('%s sends the expected request', (_name, invoke, expected) => {
      invoke()
      expect(request).toHaveBeenCalledWith(expected)
    })
  })

  describe('menu API', () => {
    const payload = { name: '用户管理', menu_type: 'C' }
    const cases = [
      ['getAllMenus', () => menuApi.getAllMenus(), { url: '/menu/get_all_menus', method: 'get' }],
      ['addMenu', () => menuApi.addMenu(payload), { url: '/menu', method: 'post', data: payload }],
      ['updateMenu', () => menuApi.updateMenu(5, payload), { url: '/menu/5', method: 'put', data: payload }],
      ['deleteMenu', () => menuApi.deleteMenu(5), { url: '/menu/5', method: 'delete' }],
      ['getMenu', () => menuApi.getMenu(5), { url: '/menu/5', method: 'get' }]
    ]

    it.each(cases)('%s sends the expected request', (_name, invoke, expected) => {
      invoke()
      expect(request).toHaveBeenCalledWith(expected)
    })
  })

  describe('department API', () => {
    const payload = { dep_name: '产品部' }
    const cases = [
      ['getDepartmentList', () => departmentApi.getDepartmentList({ page: 2, page_size: 20 }), { url: '/department', method: 'get', params: { page: 2, page_size: 20 } }],
      ['createDepartment', () => departmentApi.createDepartment(payload), { url: '/department', method: 'post', data: payload }],
      ['getDepartmentDetail', () => departmentApi.getDepartmentDetail(9), { url: '/department/9', method: 'get' }],
      ['updateDepartment', () => departmentApi.updateDepartment(9, payload), { url: '/department/9', method: 'put', data: payload }],
      ['patchDepartment', () => departmentApi.patchDepartment(9, { status: 0 }), { url: '/department/9', method: 'patch', data: { status: 0 } }],
      ['deleteDepartment', () => departmentApi.deleteDepartment(9), { url: '/department/9', method: 'delete' }]
    ]

    it.each(cases)('%s sends the expected request', (_name, invoke, expected) => {
      invoke()
      expect(request).toHaveBeenCalledWith(expected)
    })
  })
})
