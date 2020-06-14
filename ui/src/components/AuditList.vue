<template>
  <v-card outlined>
    <v-card-title>
      <v-icon class="mr-1">assignment</v-icon>Audit List
      <v-spacer />
      <v-btn class="mr-4" @click.stop="isShownAuditRegistrationDialog = true"><v-icon left>add</v-icon>New Audit</v-btn>
      <AuditRegistrationDialog v-model="isShownAuditRegistrationDialog" @updated="getAudits" />
      <ListSearchBox v-model="search" />
    </v-card-title>
    <v-data-table
      :headers="headers"
      :items="audits"
      :server-items-length="totalAudits"
      :items-per-page="defaultItemsPerPage"
      :options.sync="options"
      :loading="isAuditLoading"
      :footer-props="{
        'items-per-page-options': [5, 10, 20, 30],
      }"
      @click:row="openDetails"
    >
      <template v-slot:item.name="{ item }">
        <span class="elipsis" style="max-width: 180pt;">
          {{ item.name }}
        </span>
      </template>
      <template v-slot:item.description="{ item }">
        <span class="elipsis" style="max-width: 360pt;">
          {{ item.description }}
        </span>
      </template>
      <template v-slot:item.created_at="{ item }">
        {{ $helper.getLocalTime(item.created_at).format('YYYY-MM-DD HH:mm') }}
      </template>
      <template v-slot:item.updated_at="{ item }">
        {{ $helper.getLocalTime(item.updated_at).format('YYYY-MM-DD HH:mm') }}
      </template>
      <template v-slot:item.actions="{ item }">
        <v-icon small @click.stop="conrifmDeleteAudit(item.uuid)">delete</v-icon>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import AuditRegistrationDialog from '@/components/AuditRegistrationDialog.vue';
import ListSearchBox from '@/components/ListSearchBox.vue';

export default {
  name: 'AuditList',

  components: {
    AuditRegistrationDialog,
    ListSearchBox,
  },

  computed: {
    ...mapState(['$http']),
  },

  methods: {
    ...mapActions(['setStatus', 'setSnackbar']),
    async getAudits() {
      this.isAuditLoading = true;
      const resp = await this.$http
        .get('/audit/', {
          params: {
            q: this.search,
            page: this.options.page,
            count: this.options.itemsPerPage,
          },
        })
        .catch(() => {
          this.setStatus(500);
        });
      switch (resp.status) {
        case 200: {
          this.totalAudits = resp.data.total;
          this.audits = resp.data.audits;
          this.isAuditLoading = false;
          this.setStatus(200);
          break;
        }
        default: {
          this.setStatus(resp.status);
        }
      }
    },
    openDetails(audit) {
      const href = new URL(document.location);
      href.search = audit.uuid;
      window.open(href, '_blank');
    },
    async conrifmDeleteAudit(auditUuid) {
      if (window.confirm('Are you sure you want to delete this item?')) {
        await this.deleteAudit(auditUuid);
        this.getAudits();
      }
    },
    async deleteAudit(auditUuid) {
      const resp = await this.$http.delete(`/audit/${auditUuid}/`).catch(() => {
        this.setSnackbar({ message: 'Something went wrong while deleting the audit.', isError: true });
        this.isShownSnackbarFailure = true;
      });
      switch (resp.status) {
        case 200: {
          this.setSnackbar({ message: 'Deleted the audit successfully!', isError: false });
          break;
        }
        default: {
          this.setSnackbar({ message: `Failed to delete the audit with response code: ${resp.status}`, isError: true });
        }
      }
    },
  },

  watch: {
    options: {
      handler() {
        this.audits = [];
        this.getAudits();
      },
      deep: true,
    },
    search: {
      handler() {
        if (this.incrementalSearchTimer) {
          clearTimeout(this.incrementalSearchTimer);
        }
        this.incrementalSearchTimer = setTimeout(() => this.getAudits(), 300);
      },
    },
  },

  data: () => ({
    isAuditLoading: true,
    isShownAuditRegistrationDialog: false,
    audits: [],
    defaultItemsPerPage: 20,
    totalAudits: null,
    search: '',
    options: {},
    headers: [
      {
        text: 'Name',
        value: 'name',
        align: 'start',
        sortable: false,
        filterable: false,
        divider: false,
      },
      {
        text: 'Description',
        value: 'description',
        align: 'start',
        sortable: false,
        filterable: false,
        divider: false,
      },
      {
        text: 'Created At',
        value: 'created_at',
        align: 'start',
        sortable: false,
        filterable: false,
        divider: false,
      },
      {
        text: 'Last Updated At',
        value: 'updated_at',
        align: 'start',
        sortable: false,
        filterable: false,
        divider: false,
      },
      {
        text: 'Actions',
        value: 'actions',
        align: 'start',
        sortable: false,
        filterable: false,
        divider: false,
      },
    ],
  }),
};
</script>
