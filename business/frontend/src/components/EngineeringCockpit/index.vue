<template>
  <section class="cockpit-shell" aria-label="工程驾驶舱">
    <header class="cockpit-toolbar">
      <div>
        <strong>工程驾驶舱</strong>
        <span>规格、门禁与代码资产快照</span>
      </div>
      <el-button
        size="small"
        icon="el-icon-refresh"
        :loading="loading"
        @click="loadCockpit"
      >
        刷新
      </el-button>
    </header>

    <div v-if="loading && !cockpitHtml" class="cockpit-state">
      <i class="el-icon-loading" aria-hidden="true" />
      <span>正在加载驾驶舱</span>
    </div>
    <el-alert
      v-else-if="errorMessage"
      class="cockpit-error"
      type="error"
      :closable="false"
      show-icon
      :title="errorMessage"
    >
      <el-button size="mini" type="primary" @click="loadCockpit">
        重新加载
      </el-button>
    </el-alert>
    <iframe
      v-else
      class="cockpit-frame"
      title="工程驾驶舱内容"
      sandbox=""
      :srcdoc="cockpitHtml"
    />
  </section>
</template>

<script>
import { getCockpitSnapshot } from '@/api/cockpit'

export default {
  name: 'EngineeringCockpit',
  data() {
    return {
      loading: false,
      cockpitHtml: '',
      errorMessage: ''
    }
  },
  created() {
    this.loadCockpit()
  },
  methods: {
    async loadCockpit() {
      this.loading = true
      this.errorMessage = ''
      try {
        const response = await getCockpitSnapshot()
        const html = response && response.data && response.data.html
        if (!html) {
          throw new Error('驾驶舱快照内容为空')
        }
        this.cockpitHtml = html
      } catch (error) {
        this.errorMessage = (error && error.message) || '驾驶舱加载失败'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.cockpit-shell {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 50px);
  min-height: 620px;
  background: #eef2f6;
}

.cockpit-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 52px;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #e4e8ef;

  strong {
    display: block;
    color: #172033;
    font-size: 16px;
  }

  span {
    display: block;
    margin-top: 2px;
    color: #7b8494;
    font-size: 12px;
  }
}

.cockpit-frame {
  flex: 1;
  width: 100%;
  min-height: 0;
  border: 0;
  background: #f3f5f8;
}

.cockpit-state {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #667085;
  font-size: 14px;
}

.cockpit-state i {
  font-size: 22px;
}

.cockpit-error {
  margin: 20px;
}
</style>
