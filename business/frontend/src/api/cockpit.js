import request from '@/utils/request'

export function getCockpitSnapshot() {
  return request({
    url: '/cockpit/snapshot',
    method: 'get'
  })
}
