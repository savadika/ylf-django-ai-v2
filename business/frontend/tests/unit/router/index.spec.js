import router, {
  constantRoutes,
  notFoundRoute,
  resetRouter
} from '@/router'

describe('router baseline', () => {
  it('keeps login, 404 and root layout routes', () => {
    const paths = constantRoutes.map(route => route.path)

    expect(paths).toEqual(expect.arrayContaining(['/login', '/404', '/']))
    expect(notFoundRoute.path).toBe('*')
  })

  it('resets the router matcher without replacing the exported instance', () => {
    const originalMatcher = router.matcher

    resetRouter()

    expect(router.matcher).not.toBe(originalMatcher)
  })
})
