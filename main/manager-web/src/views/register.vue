<template>
  <div class="welcome">
    <div class="auth-left">
      <div class="auth-left-brand">
        <img alt="MekongAI" src="@/assets/mekongai-logo.png" />
        <span class="brand-name">MekongAI</span>
      </div>
      <img alt="" src="@/assets/login/register-person.png" class="auth-left-illustration" />
      <div class="auth-left-tagline">{{ $t('register.welcome') }}</div>
    </div>

    <div class="auth-right">
      <div class="auth-form-card" @keyup.enter="register">
        <div class="auth-title">{{ $t('register.title') }}</div>
        <div class="auth-subtitle">{{ $t('register.welcome') }}</div>

        <form @submit.prevent="register">
          <template v-if="!enableMobileRegister">
            <div class="auth-input">
              <el-input v-model="form.username" :placeholder="$t('register.usernamePlaceholder')" prefix-icon="el-icon-user" />
            </div>
          </template>

          <template v-if="enableMobileRegister">
            <div class="auth-input" style="display: flex; gap: 8px;">
              <el-select v-model="form.areaCode" style="width: 140px">
                <el-option v-for="item in mobileAreaList" :key="item.key" :label="`${item.name} (${item.key})`"
                  :value="item.key" />
              </el-select>
              <el-input v-model="form.mobile" :placeholder="$t('register.mobilePlaceholder')" prefix-icon="el-icon-mobile-phone" style="flex: 1" />
            </div>

            <div class="auth-captcha-row">
              <div class="auth-input">
                <el-input v-model="form.captcha" :placeholder="$t('register.captchaPlaceholder')" prefix-icon="el-icon-key" />
              </div>
              <img v-if="captchaUrl" :src="captchaUrl" alt="captcha" @click="fetchCaptcha" />
              <div v-else class="captcha-placeholder" @click="fetchCaptcha">
                <i class="el-icon-refresh"></i>
              </div>
            </div>

            <div class="auth-captcha-row">
              <div class="auth-input">
                <el-input v-model="form.mobileCaptcha" :placeholder="$t('register.mobileCaptchaPlaceholder')"
                  prefix-icon="el-icon-mobile-phone" maxlength="6" />
              </div>
              <el-button type="primary" class="send-captcha-btn" :disabled="!canSendMobileCaptcha"
                @click="sendMobileCaptcha">
                {{ countdown > 0 ? `${countdown}${$t('register.secondsLater')}` : $t('register.sendCaptcha') }}
              </el-button>
            </div>
          </template>

          <div class="auth-input">
            <el-input v-model="form.password" :placeholder="$t('register.passwordPlaceholder')" type="password"
              show-password prefix-icon="el-icon-lock" />
          </div>

          <div class="auth-input">
            <el-input v-model="form.confirmPassword" :placeholder="$t('register.confirmPasswordPlaceholder')"
              type="password" show-password prefix-icon="el-icon-lock" />
          </div>

          <div v-if="!enableMobileRegister" class="auth-captcha-row">
            <div class="auth-input">
              <el-input v-model="form.captcha" :placeholder="$t('register.captchaPlaceholder')" prefix-icon="el-icon-key" />
            </div>
            <img v-if="captchaUrl" :src="captchaUrl" alt="captcha" @click="fetchCaptcha" />
          </div>

          <div class="auth-links">
            <span @click="goToLogin">{{ $t('register.goToLogin') }}</span>
          </div>
        </form>

        <button class="auth-btn" @click="register">{{ $t('register.registerButton') }}</button>

        <div class="auth-legal">
          {{ $t('register.agreeTo') }}
          <span class="link" @click="openPage('/user-agreement.html')">{{ $t('register.userAgreement') }}</span>
          {{ $t('login.and') }}
          <span class="link" @click="openPage('/privacy-policy.html')">{{ $t('register.privacyPolicy') }}</span>
        </div>
      </div>

      <div class="auth-footer">
        <version-footer />
      </div>
    </div>
  </div>
</template>

<script>
import Api from '@/apis/api';
import VersionFooter from '@/components/VersionFooter.vue';
import { getUUID, goToPage, showDanger, showSuccess, sm2Encrypt, validateMobile } from '@/utils';
import { mapState } from 'vuex';

export default {
  name: 'register',
  components: {
    VersionFooter
  },
  computed: {
    ...mapState({
      allowUserRegister: state => state.pubConfig.allowUserRegister,
      enableMobileRegister: state => state.pubConfig.enableMobileRegister,
      mobileAreaList: state => state.pubConfig.mobileAreaList,
      sm2PublicKey: state => state.pubConfig.sm2PublicKey,
    }),
    canSendMobileCaptcha() {
      return this.countdown === 0 && validateMobile(this.form.mobile, this.form.areaCode);
    }
  },
  data() {
    return {
      form: {
        username: '',
        password: '',
        confirmPassword: '',
        captcha: '',
        captchaId: '',
        areaCode: '+86',
        mobile: '',
        mobileCaptcha: ''
      },
      captchaUrl: '',
      countdown: 0,
      timer: null,
    }
  },
  mounted() {
    this.$store.dispatch('fetchPubConfig').then(() => {
      if (!this.allowUserRegister) {
        showDanger(this.$t('register.notAllowRegister'));
        setTimeout(() => {
          goToPage('/login');
        }, 1500);
      }
    });
    this.fetchCaptcha();
  },
  methods: {
    openPage(url) {
      const lang = this.$i18n ? this.$i18n.locale : 'zh_CN';
      if (!lang.startsWith('zh')) {
        url = url.replace('.html', '-en.html');
      }
      window.open(url, '_blank');
    },
    // 复用验证码获取方法
    fetchCaptcha() {
      this.form.captchaId = getUUID();
      this.captchaUrl = `${Api.getServiceUrl()}/user/captcha?uuid=${this.form.captchaId}&t=${Date.now()}`;
    },

    // 封装输入验证逻辑
    validateInput(input, message) {
      if (!input.trim()) {
        showDanger(message);
        return false;
      }
      return true;
    },

    // 发送手机验证码
    sendMobileCaptcha() {
      if (!validateMobile(this.form.mobile, this.form.areaCode)) {
        showDanger(this.$t('register.inputCorrectMobile'));
        return;
      }

      // 验证图形验证码
      if (!this.validateInput(this.form.captcha, this.$t('register.inputCaptcha'))) {
        this.fetchCaptcha();
        return;
      }

      // 清除可能存在的旧定时器
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }

      // 开始倒计时
      this.countdown = 60;
      this.timer = setInterval(() => {
        if (this.countdown > 0) {
          this.countdown--;
        } else {
          clearInterval(this.timer);
          this.timer = null;
        }
      }, 1000);

      // 调用发送验证码接口
      Api.user.sendSmsVerification({
        phone: this.form.areaCode + this.form.mobile,
        captcha: this.form.captcha,
        captchaId: this.form.captchaId
      }, (res) => {
        showSuccess(this.$t('register.captchaSendSuccess'));
      }, (err) => {
        showDanger(err.data.msg || this.$t('register.captchaSendFailed'));
        this.countdown = 0;
        this.fetchCaptcha();
      });
    },

    // 注册逻辑
    async register() {
      if (this.enableMobileRegister) {
        // 手机号注册验证
        if (!validateMobile(this.form.mobile, this.form.areaCode)) {
          showDanger(this.$t('register.inputCorrectMobile'));
          return;
        }
        if (!this.form.mobileCaptcha) {
          showDanger(this.$t('register.requiredMobileCaptcha'));
          return;
        }
      } else {
        // 用户名注册验证
        if (!this.validateInput(this.form.username, this.$t('register.requiredUsername'))) {
          return;
        }
      }

      // 验证密码
      if (!this.validateInput(this.form.password, this.$t('register.requiredPassword'))) {
        return;
      }
      if (this.form.password !== this.form.confirmPassword) {
        showDanger(this.$t('register.passwordsNotMatch'))
        return
      }
      // 验证验证码
      if (!this.validateInput(this.form.captcha, this.$t('register.requiredCaptcha'))) {
        return;
      }
      let encryptedPassword;
      if (this.sm2PublicKey) {
        try {
          const captchaAndPassword = this.form.captcha + this.form.password;
          encryptedPassword = sm2Encrypt(this.sm2PublicKey, captchaAndPassword);
        } catch (error) {
          console.error("SM2 encryption failed:", error);
          showDanger(this.$t('sm2.encryptionFailed'));
          return;
        }
      } else {
        encryptedPassword = this.form.password;
      }

      let plainUsername;
      if (this.enableMobileRegister) {
        plainUsername = this.form.areaCode + this.form.mobile;
      } else {
        plainUsername = this.form.username;
      }

      // 准备注册数据
      const registerData = {
        username: plainUsername,
        password: encryptedPassword,
        captchaId: this.form.captchaId,
        mobileCaptcha: this.form.mobileCaptcha
      };

      Api.user.register(registerData, ({ data }) => {
        showSuccess(this.$t('register.registerSuccess'))
        this.$store.commit('clearAuth')
        goToPage('/login')
      }, (err) => {
        showDanger(err.data.msg || this.$t('register.registerFailed'))
        if (err.data != null && err.data.msg != null && err.data.msg.indexOf('图形验证码') > -1) {
          this.fetchCaptcha()
        }
      })
    },

    goToLogin() {
      goToPage('/login')
    }
  },
  beforeDestroy() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }
}
</script>

<style lang="scss" scoped>
@import './auth.scss';

.send-captcha-btn {
  margin-right: -5px;
  min-width: 100px;
  height: 40px;
  line-height: 40px;
  border-radius: 4px;
  font-size: 14px;
  background: rgb(87, 120, 255);
  border: none;
  padding: 0px;

  &:disabled {
    background: #c0c4cc;
    cursor: not-allowed;
  }
}
</style>
