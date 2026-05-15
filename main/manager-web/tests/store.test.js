/**
 * Tests for src/store/index.js — Vuex store mutations and getters.
 *
 * Since the store file creates a singleton with `new Vuex.Store(...)`,
 * we test the normalizeUserInfo logic and mutation behavior directly.
 */

jest.mock('element-ui', () => ({ Message: jest.fn() }));
jest.mock('@/router', () => ({ push: jest.fn(), replace: jest.fn() }));
jest.mock('@/utils/constant', () => ({
  default: { STORAGE_KEY: { TOKEN: 'TOKEN', USER_TYPE: 'USER_TYPE' }, PAGE: { LOGIN: '/login' } },
}));

// Minimal localStorage mock
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] ?? null),
    setItem: jest.fn((key, val) => { store[key] = String(val); }),
    removeItem: jest.fn(key => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

const store = require('@/store/index').default;

beforeEach(() => {
  localStorageMock.clear();
  jest.clearAllMocks();
});

describe('setToken / getToken', () => {
  test('stores and retrieves token', () => {
    store.commit('setToken', 'abc123');
    expect(store.state.token).toBe('abc123');
    expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'abc123');
  });
});

describe('setUserInfo', () => {
  test('normalizes super_admin to superAdmin', () => {
    store.commit('setUserInfo', { username: 'admin', super_admin: '1' });
    expect(store.state.userInfo.superAdmin).toBe(1);
  });

  test('handles null input gracefully', () => {
    store.commit('setUserInfo', null);
    expect(store.state.userInfo).toEqual({});
  });

  test('keeps existing superAdmin when present', () => {
    store.commit('setUserInfo', { superAdmin: 0 });
    expect(store.state.userInfo.superAdmin).toBe(0);
  });
});

describe('clearAuth', () => {
  test('clears state and localStorage', () => {
    store.commit('setToken', 'tok');
    store.commit('setUserInfo', { username: 'u' });
    store.commit('clearAuth');
    expect(store.state.token).toBe('');
    expect(store.state.userInfo).toEqual({});
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('userInfo');
  });
});

describe('setPubConfig', () => {
  test('stores public config', () => {
    const cfg = { version: '1.0', allowUserRegister: true, sm2PublicKey: 'abc' };
    store.commit('setPubConfig', cfg);
    expect(store.state.pubConfig).toEqual(cfg);
  });
});
