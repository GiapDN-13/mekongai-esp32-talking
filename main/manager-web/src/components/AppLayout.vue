<template>
  <div class="app-layout">
    <div class="app-topbar">
      <div class="topbar-left" @click="goHome">
        <img alt="MekongAI" src="@/assets/mekongai-logo.png" class="topbar-logo" />
        <img alt="MekongAI" src="@/assets/mekongai-text.png" class="topbar-brand" />
      </div>
      <div class="topbar-right">
        <div class="search-container" v-if="$route.path === '/home'">
          <div class="search-wrapper">
            <el-input v-model="search" :placeholder="$t('header.searchPlaceholder')" class="topbar-search"
              @keyup.enter.native="handleSearch" @focus="showSearchHistory" @blur="hideSearchHistory" clearable
              ref="searchInput" size="small">
              <i slot="prefix" class="el-icon-search"></i>
            </el-input>
            <div v-if="showHistoryPanel && searchHistory.length > 0" class="search-history-dropdown">
              <div class="search-history-header">
                <span>{{ $t("header.searchHistory") }}</span>
                <el-button type="text" size="mini" @click="clearSearchHistory">{{ $t("header.clearHistory") }}</el-button>
              </div>
              <div class="search-history-list">
                <div v-for="(item, index) in searchHistory" :key="index" class="search-history-item"
                  @click.stop="selectSearchHistory(item)">
                  <span>{{ item }}</span>
                  <i class="el-icon-close" @click.stop="removeSearchHistory(index)"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-dropdown trigger="click" @command="handleUserCommand">
          <span class="user-menu-trigger">
            <img alt="" src="@/assets/home/avatar.png" class="topbar-avatar" />
            <span class="topbar-username">{{ userInfo.username || "..." }}</span>
            <i class="el-icon-arrow-down"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item disabled class="lang-header">{{ $t("header.language") || "Language" }}</el-dropdown-item>
            <el-dropdown-item v-for="lang in languages" :key="lang.value" :command="'lang:' + lang.value"
              :class="{ 'is-active-lang': currentLanguage === lang.value }">
              {{ lang.label }}
            </el-dropdown-item>
            <el-dropdown-item divided command="changePassword">{{ $t("header.changePassword") }}</el-dropdown-item>
            <el-dropdown-item command="logout" class="logout-item">{{ $t("header.logout") }}</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </div>

    <div class="app-body">
      <nav class="app-sidebar">
        <div class="sidebar-nav">
          <div class="nav-section">
            <router-link to="/home" class="nav-item" :class="{ active: isActive('/home', '/role-config', '/device-management') }">
              <i class="el-icon-s-home"></i>
              <span>{{ $t("header.smartManagement") }}</span>
            </router-link>

            <router-link v-if="featureStatus.voiceClone" to="/voice-clone-management" class="nav-item"
              :class="{ active: isActive('/voice-clone-management') }">
              <i class="el-icon-microphone"></i>
              <span>{{ $t("header.voiceCloneManagement") }}</span>
            </router-link>

            <router-link v-if="isSuperAdmin && featureStatus.voiceClone" to="/voice-resource-management" class="nav-item"
              :class="{ active: isActive('/voice-resource-management') }">
              <i class="el-icon-headset"></i>
              <span>{{ $t("header.voiceResourceManagement") }}</span>
            </router-link>

            <router-link v-if="isSuperAdmin" to="/model-config" class="nav-item"
              :class="{ active: isActive('/model-config') }">
              <i class="el-icon-cpu"></i>
              <span>{{ $t("header.modelConfig") }}</span>
            </router-link>

            <router-link v-if="featureStatus.knowledgeBase" to="/knowledge-base-management" class="nav-item"
              :class="{ active: isActive('/knowledge-base-management', '/knowledge-file-upload') }">
              <i class="el-icon-notebook-2"></i>
              <span>{{ $t("header.knowledgeBase") }}</span>
            </router-link>
          </div>

          <div v-if="isSuperAdmin" class="nav-divider"></div>

          <div v-if="isSuperAdmin" class="nav-section">
            <div class="nav-section-title">{{ $t("header.paramDictionary") }}</div>

            <router-link to="/params-management" class="nav-item"
              :class="{ active: isActive('/params-management') }">
              <i class="el-icon-setting"></i>
              <span>{{ $t("header.paramManagement") }}</span>
            </router-link>

            <router-link to="/user-management" class="nav-item"
              :class="{ active: isActive('/user-management') }">
              <i class="el-icon-user"></i>
              <span>{{ $t("header.userManagement") }}</span>
            </router-link>

            <router-link to="/ota-management" class="nav-item"
              :class="{ active: isActive('/ota-management') }">
              <i class="el-icon-upload2"></i>
              <span>{{ $t("header.otaManagement") }}</span>
            </router-link>

            <router-link to="/dict-management" class="nav-item"
              :class="{ active: isActive('/dict-management') }">
              <i class="el-icon-collection"></i>
              <span>{{ $t("header.dictManagement") }}</span>
            </router-link>

            <router-link to="/provider-management" class="nav-item"
              :class="{ active: isActive('/provider-management') }">
              <i class="el-icon-connection"></i>
              <span>{{ $t("header.providerManagement") }}</span>
            </router-link>

            <router-link to="/agent-template-management" class="nav-item"
              :class="{ active: isActive('/agent-template-management', '/template-quick-config') }">
              <i class="el-icon-document-copy"></i>
              <span>{{ $t("header.agentTemplate") }}</span>
            </router-link>

            <router-link to="/server-side-management" class="nav-item"
              :class="{ active: isActive('/server-side-management') }">
              <i class="el-icon-monitor"></i>
              <span>{{ $t("header.serverSideManagement") }}</span>
            </router-link>

            <router-link to="/feature-management" class="nav-item"
              :class="{ active: isActive('/feature-management') }">
              <i class="el-icon-s-tools"></i>
              <span>{{ $t("header.featureManagement") }}</span>
            </router-link>
          </div>
        </div>
      </nav>

      <main class="app-content">
        <router-view @search="handleSearchFromChild" @search-reset="handleSearchReset" />
      </main>
    </div>

    <footer class="app-footer">
      <VersionFooter />
    </footer>

    <ChangePasswordDialog v-model="showPasswordDialog" />
  </div>
</template>

<script>
import userApi from "@/apis/module/user";
import i18n, { changeLanguage } from "@/i18n";
import { mapActions, mapState } from "vuex";
import ChangePasswordDialog from "./ChangePasswordDialog.vue";
import VersionFooter from "./VersionFooter.vue";
import featureManager from "@/utils/featureManager";

export default {
  name: "AppLayout",
  components: { ChangePasswordDialog, VersionFooter },
  data() {
    return {
      search: "",
      showPasswordDialog: false,
      searchHistory: [],
      showHistoryPanel: false,
      SEARCH_HISTORY_KEY: "mekongai_search_history",
      MAX_HISTORY_COUNT: 5,
    };
  },
  computed: {
    ...mapState({ userInfo: (state) => state.userInfo }),
    isSuperAdmin() {
      const u = this.userInfo || {};
      let s = u.superAdmin;
      if ((s === undefined || s === null || s === "") && u.super_admin !== undefined) s = u.super_admin;
      return Number(s) === 1;
    },
    featureStatus() {
      const f = this.$store.state.pubConfig?.systemWebMenu?.features;
      const on = (key) => !f || f[key] === undefined || f[key].enabled === undefined ? true : !!f[key].enabled;
      return { voiceClone: on("voiceClone"), knowledgeBase: on("knowledgeBase") };
    },
    currentLanguage() { return i18n.locale || "zh_CN"; },
    languages() {
      return [
        { label: this.$t("language.zhCN"), value: "zh_CN" },
        { label: this.$t("language.zhTW"), value: "zh_TW" },
        { label: this.$t("language.en"), value: "en" },
        { label: this.$t("language.de"), value: "de" },
        { label: this.$t("language.vi"), value: "vi" },
        { label: this.$t("language.ptBR"), value: "pt_BR" },
      ];
    },
  },
  async mounted() {
    this.loadSearchHistory();
    await this.syncUserProfileFromApi();
    await featureManager.waitForInitialization();
  },
  methods: {
    ...mapActions(["logout"]),
    isActive(...paths) { return paths.some((p) => this.$route.path === p); },
    goHome() { this.$router.push("/home"); },
    syncUserProfileFromApi() {
      if (!this.$store.getters.getToken) return Promise.resolve();
      return new Promise((resolve) => {
        userApi.getUserInfo((res) => {
          const data = res && res.data;
          if (data && (data.code === 0 || data.code === "0") && data.data) this.$store.commit("setUserInfo", data.data);
          resolve();
        });
      });
    },
    handleUserCommand(cmd) {
      if (cmd.startsWith("lang:")) {
        changeLanguage(cmd.slice(5));
        this.$message.success({ message: this.$t("message.success"), showClose: true });
      } else if (cmd === "changePassword") {
        this.showPasswordDialog = true;
      } else if (cmd === "logout") {
        this.logout();
        this.$message.success({ message: this.$t("message.success"), showClose: true });
      }
    },
    handleSearch() {
      const v = this.search.trim();
      if (!v) { this.$emit("search-reset"); return; }
      this.saveSearchHistory(v);
      this.handleSearchFromChild(v);
      if (this.$refs.searchInput) this.$refs.searchInput.blur();
    },
    handleSearchFromChild(keyword) {
      const homeView = this.$children.find(c => c.$options && c.$options.name === 'home');
      if (homeView && homeView.handleSearch) homeView.handleSearch(keyword);
    },
    handleSearchReset() {
      const homeView = this.$children.find(c => c.$options && c.$options.name === 'home');
      if (homeView && homeView.handleSearchReset) homeView.handleSearchReset();
    },
    showSearchHistory() { this.showHistoryPanel = true; },
    hideSearchHistory() { setTimeout(() => { this.showHistoryPanel = false; }, 200); },
    loadSearchHistory() {
      try { const h = localStorage.getItem(this.SEARCH_HISTORY_KEY); if (h) this.searchHistory = JSON.parse(h); }
      catch (e) { this.searchHistory = []; }
    },
    saveSearchHistory(kw) {
      if (!kw || this.searchHistory.includes(kw)) return;
      this.searchHistory.unshift(kw);
      if (this.searchHistory.length > this.MAX_HISTORY_COUNT) this.searchHistory = this.searchHistory.slice(0, this.MAX_HISTORY_COUNT);
      try { localStorage.setItem(this.SEARCH_HISTORY_KEY, JSON.stringify(this.searchHistory)); } catch (e) { /* noop */ }
    },
    selectSearchHistory(kw) { this.search = kw; this.handleSearch(); },
    removeSearchHistory(idx) {
      this.searchHistory.splice(idx, 1);
      try { localStorage.setItem(this.SEARCH_HISTORY_KEY, JSON.stringify(this.searchHistory)); } catch (e) { /* noop */ }
    },
    clearSearchHistory() {
      this.searchHistory = [];
      try { localStorage.removeItem(this.SEARCH_HISTORY_KEY); } catch (e) { /* noop */ }
    },
  },
};
</script>

<style lang="scss" scoped>
$primary: #4F46E5;
$primary-light: #EEF2FF;
$text-primary: #1E293B;
$text-secondary: #64748B;
$text-muted: #94A3B8;
$border: #E2E8F0;
$bg-main: #F8FAFC;
$sidebar-width: 220px;
$topbar-height: 56px;

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-main;
}

.app-topbar {
  height: $topbar-height;
  background: #fff;
  border-bottom: 1px solid $border;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  z-index: 100;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.topbar-logo {
  width: 34px;
  height: 34px;
  border-radius: 8px;
}

.topbar-brand {
  height: 22px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-container {
  position: relative;
  width: 240px;
}

.search-wrapper {
  position: relative;
}

.topbar-search ::v-deep .el-input__inner {
  border-radius: 8px;
  border: 1px solid $border;
  background: $bg-main;
  font-size: 13px;
  &:focus { border-color: $primary; }
}

.search-history-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid $border;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 1000;
}

.search-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 12px;
  color: $text-muted;
}

.search-history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: $text-secondary;
  &:hover { background: #F8FAFC; }
  .el-icon-close {
    opacity: 0;
    font-size: 11px;
    color: $text-muted;
    &:hover { color: #EF4444; }
  }
  &:hover .el-icon-close { opacity: 1; }
}

.user-menu-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s;
  &:hover { background: #F1F5F9; }
}

.topbar-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.topbar-username {
  font-size: 13px;
  font-weight: 500;
  color: $text-primary;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: $sidebar-width;
  background: #fff;
  border-right: 1px solid $border;
  overflow-y: auto;
  flex-shrink: 0;
  padding: 12px 0;
}

.sidebar-nav {
  padding: 0 8px;
}

.nav-section-title {
  font-size: 11px;
  font-weight: 600;
  color: $text-muted;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 8px 12px 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  color: $text-secondary;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s;
  margin-bottom: 2px;
  cursor: pointer;

  i {
    font-size: 16px;
    width: 20px;
    text-align: center;
    color: $text-muted;
    transition: color 0.15s;
  }

  &:hover {
    background: #F1F5F9;
    color: $text-primary;
    i { color: $text-secondary; }
  }

  &.active {
    background: $primary-light;
    color: $primary;
    font-weight: 600;
    i { color: $primary; }
  }
}

.nav-divider {
  height: 1px;
  background: $border;
  margin: 8px 12px;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.app-footer {
  background: #fff;
  border-top: 1px solid $border;
  flex-shrink: 0;
  font-size: 12px;
  color: $text-muted;
}

.lang-header {
  font-size: 11px !important;
  font-weight: 600 !important;
  color: $text-muted !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.is-active-lang {
  color: $primary !important;
  font-weight: 600;
}

.logout-item {
  color: #EF4444 !important;
}
</style>
