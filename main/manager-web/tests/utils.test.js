/**
 * Tests for src/utils/index.js — pure utility functions.
 */

// Mock element-ui and router before importing
jest.mock('element-ui', () => ({ Message: jest.fn() }));
jest.mock('@/router', () => ({ push: jest.fn(), replace: jest.fn() }));
jest.mock('@/utils/constant', () => ({
  default: { STORAGE_KEY: { TOKEN: 'TOKEN', USER_TYPE: 'USER_TYPE' }, PAGE: { LOGIN: '/login' } },
}));

const { isNull, isNotNull, validateMobile, getUUID, debounce } = require('@/utils/index');

describe('isNull', () => {
  test('undefined is null', () => expect(isNull(undefined)).toBe(true));
  test('null is null', () => expect(isNull(null)).toBe(true));
  test('empty string is null', () => expect(isNull('')).toBe(true));
  test('"undefined" string is null', () => expect(isNull('undefined')).toBe(true));
  test('"null" string is null', () => expect(isNull('null')).toBe(true));
  test('empty array is null', () => expect(isNull([])).toBe(true));
  test('non-empty string is not null', () => expect(isNull('hello')).toBe(false));
  test('number 0 is not null', () => expect(isNull(0)).toBe(false));
  test('non-empty array is not null', () => expect(isNull([1])).toBe(false));
  test('object is not null', () => expect(isNull({})).toBe(false));
});

describe('isNotNull', () => {
  test('inverse of isNull', () => {
    expect(isNotNull('hello')).toBe(true);
    expect(isNotNull(null)).toBe(false);
  });
});

describe('validateMobile', () => {
  test('China +86 valid', () => expect(validateMobile('13812345678', '+86')).toBe(true));
  test('China +86 invalid', () => expect(validateMobile('12345', '+86')).toBe(false));
  test('US +1 valid', () => expect(validateMobile('2025551234', '+1')).toBe(true));
  test('US +1 invalid (starts with 1)', () => expect(validateMobile('1025551234', '+1')).toBe(false));
  test('Japan +81 valid', () => expect(validateMobile('901234567', '+81')).toBe(true));
  test('UK +44 valid', () => expect(validateMobile('7911123456', '+44')).toBe(true));
  test('Hong Kong +852 valid', () => expect(validateMobile('51234567', '+852')).toBe(true));
  test('Korea +82 valid', () => expect(validateMobile('101234567', '+82')).toBe(true));
  test('Singapore +65 valid', () => expect(validateMobile('81234567', '+65')).toBe(true));
  test('default: 5-15 digits accepted', () => expect(validateMobile('12345', '+999')).toBe(true));
  test('strips non-digit chars', () => expect(validateMobile('138-1234-5678', '+86')).toBe(true));
});

describe('getUUID', () => {
  test('returns UUID-like string', () => {
    const uuid = getUUID();
    expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$/);
  });
  test('two calls produce different UUIDs', () => {
    expect(getUUID()).not.toBe(getUUID());
  });
});

describe('debounce', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  test('delays execution', () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 200);
    debounced();
    expect(fn).not.toHaveBeenCalled();
    jest.advanceTimersByTime(200);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  test('resets timer on multiple calls', () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 200);
    debounced();
    jest.advanceTimersByTime(100);
    debounced();
    jest.advanceTimersByTime(100);
    expect(fn).not.toHaveBeenCalled();
    jest.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  test('immediate mode calls instantly', () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 200, true);
    debounced();
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
