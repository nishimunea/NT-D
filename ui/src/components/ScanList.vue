<template>
  <div>
    <v-card outlined>
      <v-card-title>
        <v-icon class="mr-1">assessment</v-icon>Scan List
        <v-spacer />

        <v-tooltip bottom :disabled="audit.scans.length < maxScanCount" color="#CF6679">
          <template v-slot:activator="{ on }">
            <span v-on="on">
              <v-btn
                class="mr-4"
                :disabled="audit.scans.length >= maxScanCount"
                @click="isShownScanRegistrationDialog = true"
              >
                <v-icon left>add</v-icon>New Scan
              </v-btn>
            </span>
          </template>
          <span>Cannot register more than {{ maxScanCount }} scans</span>
        </v-tooltip>

        <ScanRegistrationDialog v-model="isShownScanRegistrationDialog" @updated="handleRegisteredScan" />
        <ListSearchBox v-model="search" />
      </v-card-title>
      <div @click.stop>
        <v-data-table
          :headers="headers"
          :items="audit.scans"
          :items-per-page="defaultItemsPerPage"
          :search="search"
          :loading="isAuditLoading"
          :footer-props="{
            'items-per-page-options': [5, 10, 20, 30, -1],
          }"
          :options.sync="options"
          @click:row="openDetails"
        >
          <!-- Scan Name Field -->
          <template v-slot:item.name="{ item }">
            <span class="elipsis mr-1" style="max-width: 120pt;">
              {{ item.name }}
            </span>
            <small class="d-none d-lg-inline text--disabled"> ({{ item.uuid.substring(24).toUpperCase() }}) </small>
          </template>

          <!-- Status Field -->
          <template v-slot:item.status="{ item }">
            <!-- If Scheduled -->
            <div v-if="$helper.scanStatus(item) === 'Scheduled'">
              <v-icon small class="inline">schedule</v-icon>
              Scheduled
            </div>

            <!-- If Scanning -->
            <div v-else-if="$helper.scanStatus(item) === 'Scanning'">
              <v-progress-circular indeterminate size="14" width="1" color="white" class="mr-1" />
              <span style="margin: 2px;">Scanning</span>
            </div>

            <!-- If Unscheduled -->
            <div v-else-if="$helper.scanStatus(item) === 'Unscheduled'">
              <v-icon small color="warning" class="inline mr-1">report_problem</v-icon>
              <span class="warning--text">Unscheduled</span>
            </div>

            <!-- If Completed -->
            <div v-else-if="$helper.scanStatus(item) === 'Completed'">
              <v-icon small class="inline">check_circle_outline</v-icon>
              Completed
            </div>

            <!-- If Failed -->
            <div v-else-if="$helper.scanStatus(item) === 'Failed'">
              <v-icon small color="error" class="inline mr-1">report_problem</v-icon>
              <span class="error--text">Failed</span>
            </div>
          </template>

          <!-- Scan Description Field -->
          <template v-slot:item.description="{ item }">
            <span class="elipsis" style="max-width: 180pt;">{{ item.description }}</span>
          </template>

          <!-- Scan Target Field -->
          <template v-slot:item.target="{ item }">
            <span class="elipsis mr-1" style="max-width: 100pt;">
              {{ item.target }}
              <v-icon v-if="item.rrule" small>loop</v-icon>
            </span>
          </template>

          <!-- Detector Module Field -->
          <template v-slot:item.detection_module="{ item }">
            <v-tooltip bottom color="grey darken-3">
              <template v-slot:activator="{ on }">
                <span v-on="on">{{ item.detection_module }}</span>
              </template>
              <span>
                {{ item.detection_mode }}
              </span>
            </v-tooltip>
          </template>

          <!-- Last Updated At Field -->
          <template v-slot:item.updated_at="{ item }">
            <div class="elipsis" style="max-width: 100pt;">
              {{ $helper.getLocalTime(item.updated_at).format('YYYY-MM-DD hh:mm') }}
            </div>
          </template>

          <!-- Actions Field -->
          <template v-slot:item.actions="{ item }">
            <!-- Cancel Button -->
            <v-tooltip v-if="item.scheduled_at" bottom color="grey darken-3">
              <template v-slot:activator="{ on }">
                <v-icon small v-on="on" class="mr-2" @click.stop="conrifmDeleteSchedule(item.uuid)">
                  timer_off
                </v-icon>
              </template>
              <span>
                Cancel
              </span>
            </v-tooltip>

            <!-- Schedule Button -->
            <v-tooltip v-else bottom color="grey darken-3">
              <template v-slot:activator="{ on }">
                <v-icon v-on="on" small class="mr-2" @click.stop="openScheduleDialog(item)">
                  timer
                </v-icon>
              </template>
              <span>
                Schedule scan
              </span>
            </v-tooltip>

            <!-- Delete Button -->
            <v-tooltip bottom color="grey darken-3">
              <template v-slot:activator="{ on }">
                <v-icon small v-on="on" @click.stop="conrifmDeleteScan(item.uuid)">delete</v-icon>
              </template>
              <span>
                Delete scan
              </span>
            </v-tooltip>
          </template>
        </v-data-table>
      </div>
    </v-card>

    <div @click.stop>
      <ScanStatusDrawer />
    </div>

    <CautionDialog v-model="isShownCaution" />
    <ScanScheduleDialog v-model="isShownScheduleDialog" />
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import CautionDialog from '@/components/CautionDialog.vue';
import ListSearchBox from '@/components/ListSearchBox.vue';
import ScanRegistrationDialog from '@/components/ScanRegistrationDialog.vue';
import ScanStatusDrawer from '@/components/ScanStatusDrawer.vue';
import ScanScheduleDialog from '@/components/ScanScheduleDialog.vue';

export default {
  name: 'ScanList',

  components: {
    CautionDialog,
    ListSearchBox,
    ScanRegistrationDialog,
    ScanStatusDrawer,
    ScanScheduleDialog,
  },

  computed: {
    ...mapState(['audit', 'currentAuditUUID', 'isPolicyAccepted', '$http']),
  },

  methods: {
    ...mapActions([
      'updateScan',
      'setAudit',
      'setCurrentScan',
      'setIsShownScanStatusDrawer',
      'setStatus',
      'setSnackbar',
    ]),
    async getAudit() {
      this.isAuditLoading = true;
      const resp = await this.$http.get(`/audit/${this.currentAuditUUID}/`).catch(() => {
        this.setStatus(500);
      });
      switch (resp.status) {
        case 200: {
          this.isAuditLoading = false;
          this.setAudit(resp.data);
          this.setStatus(200);
          window.document.title = `${process.env.VUE_APP_TITLE} - ${resp.data.name}`;
          break;
        }
        default: {
          this.setStatus(resp.status);
        }
      }
    },
    handleRegisteredScan(registeredScan) {
      this.getAudit();
      this.openScheduleDialog(registeredScan);
    },
    openDetails(scan) {
      if (this.$helper.scanStatus(scan) === 'Unscheduled') {
        this.openScheduleDialog(scan);
      } else {
        this.openScanStatusDrawer(scan);
      }
    },
    openScanStatusDrawer(scan) {
      this.setCurrentScan(scan);
      this.setIsShownScanStatusDrawer(true);
    },
    openScheduleDialog(scan) {
      this.setCurrentScan(scan);
      this.isShownScheduleDialog = true;
    },
    conrifmDeleteSchedule(scanUuid) {
      if (window.confirm('Are you sure you want to cancel the scan schedule?')) {
        this.deleteSchedule(scanUuid);
      }
    },
    async deleteSchedule(scanUuid) {
      const resp = await this.$http.delete(`/scan/${scanUuid}/schedule/`).catch(() => {
        this.setSnackbar({ message: 'Something went wrong while cancelling the schedule.', isError: true });
      });
      switch (resp.status) {
        case 200: {
          this.setSnackbar({ message: 'Cancelled the schedule successfully!', isError: false });
          this.updateScan(resp.data);
          break;
        }
        default: {
          this.setSnackbar({
            message: `Failed to cancel the schedule with response code: ${resp.status}`,
            isError: true,
          });
        }
      }
    },
    conrifmDeleteScan(scanUuid) {
      if (window.confirm('Are you sure you want to delete this item?')) {
        this.deleteScan(scanUuid);
        this.getAudit();
      }
    },
    async deleteScan(scanUuid) {
      const resp = await this.$http.delete(`/scan/${scanUuid}/`).catch(() => {
        this.setSnackbar({ message: 'Something went wrong while deleting the scan.', isError: true });
      });
      switch (resp.status) {
        case 200: {
          this.setSnackbar({ message: 'Deleted the scan successfully!', isError: false });
          break;
        }
        default: {
          this.setSnackbar({ message: `Failed to delete the scan with response code: ${resp.status}`, isError: true });
        }
      }
    },
  },

  data: () => ({
    isShownCaution: false,
    isShownScanRegistrationDialog: false,
    isShownScheduleDialog: false,
    isAuditLoading: true,
    defaultItemsPerPage: 20,
    maxScanCount: Number(process.env.VUE_APP_MAX_SCAN_COUNT),
    options: { sortBy: ['updated_at'], sortDesc: [true] },
    reloadInterval: Number(process.env.VUE_APP_SCAN_RELOAD_INTERVAL),
    search: '',
    headers: [
      {
        text: 'Name',
        value: 'name',
        align: 'start',
        sortable: true,
        filterable: true,
        divider: false,
      },
      {
        text: 'Status',
        value: 'status',
        align: 'start',
        sortable: false,
        filterable: false,
        divider: false,
      },
      {
        text: 'Description',
        value: 'description',
        align: 'start',
        sortable: true,
        filterable: true,
        divider: false,
      },
      {
        text: 'Target',
        value: 'target',
        align: 'start',
        sortable: true,
        filterable: true,
        divider: false,
      },
      {
        text: 'Detector',
        value: 'detection_module',
        align: 'start',
        sortable: true,
        filterable: true,
        divider: false,
      },
      {
        text: 'Last Updated At',
        value: 'updated_at',
        align: 'start',
        sortable: true,
        filterable: true,
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

  mounted() {
    if (!this.isPolicyAccepted) {
      this.isShownCaution = true;
    }
  },

  created() {
    this.getAudit();
    setInterval(this.getAudit, this.reloadInterval);
  },
};
</script>
