import Vue from 'vue'
import VueRouter from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'welcome',
    component: () => import('../views/login.vue')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/register.vue')
  },
  {
    path: '/retrieve-password',
    name: 'RetrievePassword',
    component: () => import('../views/retrievePassword.vue')
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: 'home',
        name: 'home',
        component: () => import('../views/home.vue')
      },
      {
        path: 'role-config',
        name: 'RoleConfig',
        component: () => import('../views/roleConfig.vue')
      },
      {
        path: 'voice-print',
        name: 'VoicePrint',
        component: () => import('../views/VoicePrint.vue')
      },
      {
        path: 'device-management',
        name: 'DeviceManagement',
        component: () => import('../views/DeviceManagement.vue')
      },
      {
        path: 'user-management',
        name: 'UserManagement',
        component: () => import('../views/UserManagement.vue')
      },
      {
        path: 'model-config',
        name: 'ModelConfig',
        component: () => import('../views/ModelConfig.vue')
      },
      {
        path: 'params-management',
        name: 'ParamsManagement',
        component: () => import('../views/ParamsManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'knowledge-base-management',
        name: 'KnowledgeBaseManagement',
        component: () => import('../views/KnowledgeBaseManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'knowledge-file-upload',
        name: 'KnowledgeFileUpload',
        component: () => import('../views/KnowledgeFileUpload.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'server-side-management',
        name: 'ServerSideManager',
        component: () => import('../views/ServerSideManager.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'ota-management',
        name: 'OtaManagement',
        component: () => import('../views/OtaManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'voice-resource-management',
        name: 'VoiceResourceManagement',
        component: () => import('../views/VoiceResourceManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'voice-clone-management',
        name: 'VoiceCloneManagement',
        component: () => import('../views/VoiceCloneManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'dict-management',
        name: 'DictManagement',
        component: () => import('../views/DictManagement.vue')
      },
      {
        path: 'provider-management',
        name: 'ProviderManagement',
        component: () => import('../views/ProviderManagement.vue')
      },
      {
        path: 'agent-template-management',
        name: 'AgentTemplateManagement',
        component: () => import('../views/AgentTemplateManagement.vue')
      },
      {
        path: 'template-quick-config',
        name: 'TemplateQuickConfig',
        component: () => import('../views/TemplateQuickConfig.vue')
      },
      {
        path: 'feature-management',
        name: 'FeatureManagement',
        component: () => import('../views/FeatureManagement.vue'),
        meta: { requiresAuth: true }
      },
    ]
  },
]

const router = new VueRouter({
  base: process.env.VUE_APP_PUBLIC_PATH || '/',
  routes
})

const originalPush = VueRouter.prototype.push
VueRouter.prototype.push = function push(location) {
  return originalPush.call(this, location).catch(err => {
    if (err.name === 'NavigationDuplicated') {
      window.location.reload()
    } else {
      throw err
    }
  })
}

const protectedRoutes = ['home', 'RoleConfig', 'DeviceManagement', 'UserManagement', 'ModelConfig', 'KnowledgeBaseManagement', 'KnowledgeFileUpload']

router.beforeEach((to, from, next) => {
  if (protectedRoutes.includes(to.name) || (to.meta && to.meta.requiresAuth)) {
    const token = localStorage.getItem('token')
    if (!token) {
      next({ name: 'login', query: { redirect: to.fullPath } })
      return
    }
  }
  next()
})

export default router
