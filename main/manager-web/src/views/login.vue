<template>
  <div class="welcome">
    <div class="auth-left">
      <div class="auth-left-brand">
        <img alt="MekongAI" src="@/assets/mekongai-logo.png" />
        <span class="brand-name">MekongAI</span>
      </div>
      <img alt="" src="@/assets/login/login-person.png" class="auth-left-illustration" />
      <div class="auth-left-tagline">{{ $t("login.welcome") }}</div>
    </div>

    <div class="auth-right">
      <el-dropdown trigger="click" class="auth-lang-dropdown" @visible-change="handleLanguageDropdownVisibleChange">
        <span class="el-dropdown-link">
          {{ currentLanguageText }}
          <i class="el-icon-arrow-down el-icon--right" :class="{ 'rotate-down': languageDropdownVisible }"></i>
        </span>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item @click.native="changeLanguage('zh_CN')">{{ $t("language.zhCN") }}</el-dropdown-item>
          <el-dropdown-item @click.native="changeLanguage('zh_TW')">{{ $t("language.zhTW") }}</el-dropdown-item>
          <el-dropdown-item @click.native="changeLanguage('en')">{{ $t("language.en") }}</el-dropdown-item>
          <el-dropdown-item @click.native="changeLanguage('de')">{{ $t("language.de") }}</el-dropdown-item>
          <el-dropdown-item @click.native="changeLanguage('vi')">{{ $t("language.vi") }}</el-dropdown-item>
          <el-dropdown-item @click.native="changeLanguage('pt_BR')">{{ $t("language.ptBR") }}</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>

      <div class="auth-form-card" @keyup.enter="login">
        <div class="auth-title">{{ $t("login.title") }}</div>
        <div class="auth-subtitle">{{ $t("login.welcome") }}</div>

        <template v-if="!isMobileLogin">
          <div class="auth-input">
            <el-input v-model="form.username" :placeholder="$t('login.usernamePlaceholder')" prefix-icon="el-icon-user" />
          </div>
        </template>
        <template v-else>
          <div class="auth-input" style="display: flex; gap: 8px;">
            <el-select v-model="form.areaCode" style="width: 140px">
              <el-option v-for="item in mobileAreaList" :key="item.key" :label="`${item.name} (${item.key})`" :value="item.key" />
            </el-select>
            <el-input v-model="form.mobile" :placeholder="$t('login.mobilePlaceholder')" prefix-icon="el-icon-mobile-phone" style="flex:1" />
          </div>
        </template>

        <div class="auth-input">
          <el-input v-model="form.password" :placeholder="$t('login.passwordPlaceholder')" type="password" show-password prefix-icon="el-icon-lock" />
        </div>

        <div class="auth-captcha-row">
          <div class="auth-input">
            <el-input v-model="form.captcha" :placeholder="$t('login.captchaPlaceholder')" prefix-icon="el-icon-key" />
          </div>
          <img v-if="captchaUrl" :src="captchaUrl" alt="captcha" @click="fetchCaptcha" />
          <div v-else class="captcha-placeholder" @click="fetchCaptcha">
            <i class="el-icon-refresh"></i>
          </div>
        </div>

        <div class="auth-links">
          <span @click="goToRegister">{{ $t("login.register") }}</span>
          <span v-if="enableMobileRegister" @click="goToForgetPassword">{{ $t("login.forgetPassword") }}</span>
        </div>

        <button class="auth-btn" @click="login">{{ $t("login.login") }}</button>

        <div class="auth-login-type" v-if="enableMobileRegister">
          <el-tooltip :content="$t('login.mobileLogin')" placement="bottom">
            <el-button :type="isMobileLogin ? 'primary' : 'default'" icon="el-icon-mobile" circle size="small"
              @click="switchLoginType('mobile')"></el-button>
          </el-tooltip>
          <el-tooltip :content="$t('login.usernameLogin')" placement="bottom">
            <el-button :type="!isMobileLogin ? 'primary' : 'default'" icon="el-icon-user" circle size="small"
              @click="switchLoginType('username')"></el-button>
          </el-tooltip>
        </div>

        <div class="auth-legal">
          {{ $t("login.agreeTo") }}
          <span class="link" @click="openPage('/user-agreement.html')">{{ $t("login.userAgreement") }}</span>
          {{ $t("login.and") }}
          <span class="link" @click="openPage('/privacy-policy.html')">{{ $t("login.privacyPolicy") }}</span>
        </div>
      </div>

      <div class="auth-footer">
        <version-footer />
      </div>
    </div>
  </div>
</template>

<script>
import Api from "@/apis/api";
import userApi from "@/apis/module/user";
import VersionFooter from "@/components/VersionFooter.vue";
import i18n, { changeLanguage } from "@/i18n";
import { getUUID, goToPage, showDanger, showSuccess, sm2Encrypt, validateMobile } from "@/utils";
import { mapState } from "vuex";

export default {
  name: "login",
  components: { VersionFooter },
  computed: {
    ...mapState({
      allowUserRegister: (state) => state.pubConfig.allowUserRegister,
      enableMobileRegister: (state) => state.pubConfig.enableMobileRegister,
      mobileAreaList: (state) => state.pubConfig.mobileAreaList,
      sm2PublicKey: (state) => state.pubConfig.sm2PublicKey,
    }),
    currentLanguage() { return i18n.locale || "zh_CN"; },
    currentLanguageText() {
      const map = { zh_CN: "language.zhCN", zh_TW: "language.zhTW", en: "language.en", de: "language.de", vi: "language.vi", pt_BR: "language.ptBR" };
      return this.$t(map[this.currentLanguage] || "language.zhCN");
    },
  },
  data() {
    return {
      form: { username: "", password: "", captcha: "", captchaId: "", areaCode: "+86", mobile: "" },
      captchaUuid: "",
      captchaUrl: "",
      isMobileLogin: false,
      languageDropdownVisible: false,
    };
  },
  mounted() {
    this.fetchCaptcha();
    this.$store.dispatch("fetchPubConfig").then(() => {
      this.isMobileLogin = this.enableMobileRegister;
    });
  },
  methods: {
    openPage(url) {
      const lang = this.$i18n ? this.$i18n.locale : 'zh_CN';
      if (!lang.startsWith('zh')) url = url.replace('.html', '-en.html');
      window.open(url, '_blank');
    },
    fetchCaptcha() {
      const token = localStorage.getItem('token');
      if (token) {
        if (this.$route.path !== "/home") this.$router.push("/home");
      } else {
        this.captchaUuid = getUUID();
        this.captchaUrl = `${Api.getServiceUrl()}/user/captcha?uuid=${this.captchaUuid}&t=${Date.now()}`;
      }
    },
    handleLanguageDropdownVisibleChange(visible) { this.languageDropdownVisible = visible; },
    changeLanguage(lang) {
      changeLanguage(lang);
      this.languageDropdownVisible = false;
      this.$message.success({ message: this.$t("message.success"), showClose: true });
    },
    switchLoginType(type) {
      this.isMobileLogin = type === "mobile";
      this.form.username = "";
      this.form.mobile = "";
      this.form.password = "";
      this.form.captcha = "";
      this.fetchCaptcha();
    },
    validateInput(input, messageKey) {
      if (!input.trim()) { showDanger(this.$t(messageKey)); return false; }
      return true;
    },
    getUserInfo() {
      userApi.getUserInfo(({ data }) => {
        if (data.code === 0) {
          this.$store.commit("setUserInfo", data.data);
          goToPage("/home");
        }
      });
    },
    async login() {
      if (this.isMobileLogin) {
        if (!validateMobile(this.form.mobile, this.form.areaCode)) { showDanger(this.$t('login.requiredMobile')); return; }
        this.form.username = this.form.areaCode + this.form.mobile;
      } else {
        if (!this.validateInput(this.form.username, 'login.requiredUsername')) return;
      }
      if (!this.validateInput(this.form.password, 'login.requiredPassword')) return;
      if (!this.validateInput(this.form.captcha, 'login.requiredCaptcha')) return;

      let encryptedPassword;
      if (this.sm2PublicKey) {
        try {
          encryptedPassword = sm2Encrypt(this.sm2PublicKey, this.form.captcha + this.form.password);
        } catch (error) {
          showDanger(this.$t('sm2.encryptionFailed'));
          return;
        }
      } else {
        encryptedPassword = this.form.password;
      }

      this.form.captchaId = this.captchaUuid;
      userApi.login(
        { username: this.form.username, password: encryptedPassword, captchaId: this.form.captchaId },
        ({ data }) => {
          showSuccess(this.$t('login.loginSuccess'));
          this.$store.commit("setToken", JSON.stringify(data.data));
          this.getUserInfo();
        },
        (err) => {
          const msg = (err && err.data && err.data.msg) ? err.data.msg : "Login failed";
          showDanger(msg);
        }
      );
      setTimeout(() => { this.fetchCaptcha(); }, 1000);
    },
    goToRegister() { goToPage("/register"); },
    goToForgetPassword() { goToPage("/retrieve-password"); },
  },
};
</script>

<style lang="scss" scoped>
@import "./auth.scss";
</style>
