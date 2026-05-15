<template>
  <div class="welcome">
    <div class="auth-left">
      <div class="auth-left-brand">
        <img alt="MekongAI" src="@/assets/mekongai-logo.png" />
        <span class="brand-name">MekongAI</span>
      </div>
      <img alt="" src="@/assets/login/register-person.png" class="auth-left-illustration" />
    </div>

    <div class="auth-right">
      <div class="auth-form-card" @keyup.enter="retrievePassword">
        <div class="auth-title">{{ $t('retrievePassword.title') }}</div>
        <div class="auth-subtitle">{{ $t('retrievePassword.subtitle') }}</div>

        <form @submit.prevent="retrievePassword">
          <div class="auth-input" style="display: flex; gap: 8px;">
            <el-select v-model="form.areaCode" style="width: 140px">
              <el-option v-for="item in mobileAreaList" :key="item.key" :label="`${item.name} (${item.key})`"
                :value="item.key" />
            </el-select>
            <el-input v-model="form.mobile" :placeholder="$t('retrievePassword.mobilePlaceholder')" prefix-icon="el-icon-mobile-phone" style="flex: 1" />
          </div>

          <div class="auth-captcha-row">
            <div class="auth-input">
              <el-input v-model="form.captcha" :placeholder="$t('retrievePassword.captchaPlaceholder')" prefix-icon="el-icon-key" />
            </div>
            <img v-if="captchaUrl" :src="captchaUrl" alt="captcha" @click="fetchCaptcha" />
            <div v-else class="captcha-placeholder" @click="fetchCaptcha">
              <i class="el-icon-refresh"></i>
            </div>
          </div>

          <div class="auth-captcha-row">
            <div class="auth-input">
              <el-input v-model="form.mobileCaptcha" :placeholder="$t('retrievePassword.mobileCaptchaPlaceholder')"
                prefix-icon="el-icon-message" maxlength="6" />
            </div>
            <el-button type="primary" class="send-captcha-btn" :disabled="!canSendMobileCaptcha"
              @click="sendMobileCaptcha">
              {{ countdown > 0 ? `${countdown}${$t('register.secondsLater')}` : $t('retrievePassword.getMobileCaptcha') }}
            </el-button>
          </div>

          <div class="auth-input">
            <el-input v-model="form.newPassword" :placeholder="$t('retrievePassword.newPasswordPlaceholder')" type="password" show-password prefix-icon="el-icon-lock" />
          </div>

          <div class="auth-input">
            <el-input v-model="form.confirmPassword" :placeholder="$t('retrievePassword.confirmNewPasswordPlaceholder')" type="password" show-password prefix-icon="el-icon-lock" />
          </div>

          <div class="auth-links">
            <span @click="goToLogin">{{ $t('retrievePassword.goToLogin') }}</span>
          </div>

          <button type="button" class="auth-btn" @click="retrievePassword">{{ $t('retrievePassword.resetButton') }}</button>

          <div class="auth-legal">
            {{ $t('retrievePassword.agreeTo') }}
            <span class="link" @click="openPage('/user-agreement.html')">{{ $t('register.userAgreement') }}</span>
            {{ $t('login.and') }}
            <span class="link" @click="openPage('/privacy-policy.html')">{{ $t('register.privacyPolicy') }}</span>
          </div>
        </form>
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
import { getUUID, goToPage, showDanger, showSuccess, validateMobile, sm2Encrypt } from '@/utils';
import { mapState } from 'vuex';

export default {
  name: 'retrieve',
  components: {
    VersionFooter
  },
  computed: {
    ...mapState({
      allowUserRegister: state => state.pubConfig.allowUserRegister,
      mobileAreaList: state => state.pubConfig.mobileAreaList,
      sm2PublicKey: state => state.pubConfig.sm2PublicKey
    }),
    canSendMobileCaptcha() {
      return this.countdown === 0 && validateMobile(this.form.mobile, this.form.areaCode);
    }
  },
  data() {
    return {
      form: {
        areaCode: '+86',
        mobile: '',
        captcha: '',
        captchaId: '',
        mobileCaptcha: '',
        newPassword: '',
        confirmPassword: ''
      },
      captchaUrl: '',
      countdown: 0,
      timer: null
    }
  },
  mounted() {
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
        showDanger(this.$t('retrievePassword.inputCorrectMobile'));
        return;
      }

      // 验证图形验证码
      if (!this.validateInput(this.form.captcha, this.$t('retrievePassword.captchaRequired'))) {
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
        showSuccess(this.$t('retrievePassword.captchaSendSuccess'));
      }, (err) => {
        showDanger(err.data.msg || this.$t('register.captchaSendFailed'));
        this.countdown = 0;
        this.fetchCaptcha();
      });
    },

    // 修改逻辑
    retrievePassword() {
      // 验证逻辑
      if (!validateMobile(this.form.mobile, this.form.areaCode)) {
        showDanger(this.$t('retrievePassword.inputCorrectMobile'));
        return;
      }
      if (!this.form.captcha) {
        showDanger(this.$t('retrievePassword.captchaRequired'));
        return;
      }
      if (!this.form.mobileCaptcha) {
        showDanger(this.$t('retrievePassword.mobileCaptchaRequired'));
        return;
      }
      if (this.form.newPassword !== this.form.confirmPassword) {
        showDanger(this.$t('retrievePassword.passwordsNotMatch'));
        return;
      }

      let encryptedPassword;
      if (this.sm2PublicKey) {
        try {
          const captchaAndPassword = this.form.captcha + this.form.newPassword;
          encryptedPassword = sm2Encrypt(this.sm2PublicKey, captchaAndPassword);
        } catch (error) {
          console.error("SM2 encryption failed:", error);
          showDanger(this.$t('sm2.encryptionFailed'));
          return;
        }
      } else {
        encryptedPassword = this.form.newPassword;
      }

      Api.user.retrievePassword({
        phone: this.form.areaCode + this.form.mobile,
        password: encryptedPassword,
        code: this.form.mobileCaptcha,
        captchaId: this.form.captchaId
      }, (res) => {
        showSuccess(this.$t('retrievePassword.passwordUpdateSuccess'));
        goToPage('/login');
      }, (err) => {
        showDanger(err.data.msg || this.$t('message.error'));
        if (err.data != null && err.data.msg != null && (err.data.msg.indexOf('图形验证码') > -1 || err.data.msg.indexOf('Captcha') > -1)) {
          this.fetchCaptcha()
        }
      });
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
</style>
