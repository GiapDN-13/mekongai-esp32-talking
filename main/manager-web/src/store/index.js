import { goToPage } from "@/utils";
import Vue from 'vue';
import Vuex from 'vuex';
import Constant from '../utils/constant';

Vue.use(Vuex)

function normalizeUserInfo(raw) {
  if (!raw || typeof raw !== 'object') {
    return {};
  }
  const u = { ...raw };
  if (u.superAdmin === undefined && u.super_admin !== undefined) {
    u.superAdmin = u.super_admin;
  }
  if (u.superAdmin !== undefined && u.superAdmin !== null && u.superAdmin !== '') {
    const n = Number(u.superAdmin);
    if (!Number.isNaN(n)) {
      u.superAdmin = n;
    }
  }
  return u;
}

export default new Vuex.Store({
  state: {
    token: '',
    userInfo: {}, // 添加用户信息存储
    pubConfig: { // 添加公共配置存储
      version: '',
      beianIcpNum: 'null',
      beianGaNum: 'null',
      allowUserRegister: false,
      sm2PublicKey: ''
    }
  },
  getters: {
    getToken(state) {
      if (!state.token) {
        state.token = localStorage.getItem('token')
      }
      return state.token
    },
    getUserInfo(state) {
      return state.userInfo
    },
    getPubConfig(state) {
      return state.pubConfig
    }
  },
  mutations: {
    setToken(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },
    setUserInfo(state, userInfo) {
      const normalized = normalizeUserInfo(userInfo)
      state.userInfo = normalized
      localStorage.setItem('userInfo', JSON.stringify(normalized))
    },
    setPubConfig(state, config) {
      state.pubConfig = config
      localStorage.setItem('pubConfig', JSON.stringify(config))
    },
    clearAuth(state) {
      state.token = ''
      state.userInfo = {}
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
    }
  },
  actions: {
    // 添加 logout action
    logout({ commit }) {
      return new Promise((resolve) => {
        commit('clearAuth')
        goToPage(Constant.PAGE.LOGIN, true);
      })
    },
    // 添加获取公共配置的 action
    fetchPubConfig({ commit }) {
      const user = require('../apis/module/user.js').default;
      return new Promise((resolve) => {
        user.getPubConfig(({ data }) => {
          if (data.code === 0) {
            commit('setPubConfig', data.data);
          }
          resolve();
        });
      });
    }
  },
  modules: {
  }
})