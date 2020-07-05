<template>
  <div>
    <v-menu>
      <template v-slot:activator="{ on }">
        <v-btn icon v-on="on">
          <v-icon>menu</v-icon>
        </v-btn>
      </template>

      <v-list dense>
        <v-list-item v-if="isIntegrationEnabled('slack')" @click="conrifmDisableIntegration('slack')">
          <v-list-item-icon>
            <v-icon>swap_horiz</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Disable Slack Integration</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item v-else @click="isShownIntegrationSlackDialog = true">
          <v-list-item-icon>
            <v-icon>swap_horiz</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Enable Slack Integration</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item @click="setReportComponent('AuditReportHtml')">
          <v-list-item-icon>
            <v-icon>get_app</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Export Audit Results</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-divider />

        <v-list-item @click="conrifmLogout">
          <v-list-item-icon>
            <v-icon>exit_to_app</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-menu>
    <IntegrationSlackDialog v-model="isShownIntegrationSlackDialog" />
    <div v-show="false">
      <component v-bind:is="reportComponent" ref="report" v-on:loaded="downloadReport" />
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import IntegrationSlackDialog from '@/components/IntegrationSlackDialog.vue';
import AuditReportHtml from '@/components/exports/AuditReportHtml.vue';

export default {
  name: 'ScanMenu',

  components: {
    IntegrationSlackDialog,
    AuditReportHtml,
  },

  computed: {
    ...mapState(['currentAudit', 'currentAuditUUID', '$http']),
  },

  methods: {
    ...mapActions(['forgetToken', 'setSnackbar']),
    isIntegrationEnabled(service) {
      const integrations = this.currentAudit.integrations || undefined;
      return integrations && integrations.findIndex((item) => item.service === service) >= 0;
    },
    conrifmDisableIntegration(service) {
      if (window.confirm(`Are you sure you want to disable ${service} integration?`)) {
        this.disableIntegration(service);
      }
    },
    conrifmLogout() {
      if (window.confirm('Are you sure you want to log out?')) {
        this.forgetToken();
        window.location.reload();
      }
    },
    async disableIntegration(service) {
      const resp = await this.$http.delete(`/audit/${this.currentAuditUUID}/integration/${service}/`).catch(() => {
        this.setSnackbar({ message: `Something went wrong while disabling ${service} integration`, isError: true });
      });
      switch (resp.status) {
        case 200: {
          window.location.reload();
          break;
        }
        default: {
          this.setSnackbar({ message: resp.data.message, isError: true });
        }
      }
    },
    downloadReport() {
      const url = window.URL.createObjectURL(new Blob([this.$refs.report.$el.outerHTML], { type: 'text/html' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${this.currentAuditUUID}.html`);
      document.body.appendChild(link);
      link.click();
    },
    setReportComponent(component) {
      this.reportComponent = undefined;
      this.$nextTick(() => {
        this.reportComponent = component;
      });
    },
  },

  data: () => ({
    reportComponent: undefined,
    isShownIntegrationSlackDialog: false,
  }),
};
</script>
