import Vue from 'vue';
import Vuex from 'vuex';

const accessTokenKey = 'NTD_TOKEN';
const policyAccepted = 'NTD_POLICY_ACCEPTED';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    apiEndpoint: process.env.VUE_APP_API_ENDPOINT,
    apiTimeout: Number(process.env.VUE_APP_API_TIMEOUT),
    currentAudit: {
      scans: [],
    },
    currentAuditUUID: '',
    currentScan: {},
    currentScanUUID: '',
    isPolicyAccepted: Boolean(localStorage.getItem(policyAccepted) === 'true'),
    isShownScanStatusDrawer: false,
    status: 0,
    snackbar: { message: '', isError: false },
    token: localStorage.getItem(accessTokenKey),
    $http: null,
  },
  mutations: {
    setCurrentAudit(state, audit) {
      state.currentAudit = audit;
    },
    setCurrentAuditUUID(state, auditUUID) {
      state.currentAuditUUID = auditUUID;
    },
    setCurrentScan(state, scan) {
      state.currentScan = scan;
    },
    setCurrentScanUUID(state, scanUUID) {
      state.currentScanUUID = scanUUID;
    },
    setIsPolicyAccepted(state, isAccepted) {
      state.isPolicyAccepted = isAccepted;
    },
    setIsShownScanStatusDrawer(state, isShown) {
      state.isShownScanStatusDrawer = isShown;
    },
    setStatus(state, status) {
      state.status = status;
    },
    setSnackbar(state, content) {
      state.snackbar = content;
    },
    setHTTPClient(state, client) {
      state.$http = client;
    },
    setToken(state, token) {
      state.token = token;
    },
    updateScan(state, scan) {
      const index = state.currentAudit.scans.findIndex((e) => e.uuid === scan.uuid);
      Vue.set(state.currentAudit.scans, index, scan);
    },
  },
  actions: {
    forgetToken({ commit }) {
      localStorage.removeItem(accessTokenKey);
      commit('setToken', null);
    },
    setCurrentAudit({ commit }, audit) {
      commit('setCurrentAudit', audit);
    },
    setCurrentAuditUUID({ commit }, auditUUID) {
      commit('setCurrentAuditUUID', auditUUID);
    },
    setCurrentScan({ commit }, scan) {
      commit('setCurrentScan', scan);
    },
    setCurrentScanUUID({ commit }, scanUUID) {
      commit('setCurrentScanUUID', scanUUID);
    },
    setIsPolicyAccepted({ commit }, isAccepted) {
      localStorage.setItem(policyAccepted, String(isAccepted));
      commit('setIsPolicyAccepted', isAccepted);
    },
    setIsShownScanStatusDrawer({ commit }, isShown) {
      commit('setIsShownScanStatusDrawer', isShown);
    },
    setStatus({ commit }, status) {
      commit('setStatus', parseInt(status, 10));
    },
    setSnackbar({ commit }, content) {
      const message = String(content.message);
      const isError = String(content.isError).toLowerCase() === 'true';
      commit('setSnackbar', { message, isError });
    },
    setHTTPClient({ commit }, client) {
      commit('setHTTPClient', client);
    },
    setToken({ commit }, token) {
      localStorage.setItem(accessTokenKey, token);
      commit('setToken', token);
    },
    updateScan({ commit }, scan) {
      commit('updateScan', scan);
    },
  },
  modules: {},
});
