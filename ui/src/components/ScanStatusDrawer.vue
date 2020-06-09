<template>
  <v-navigation-drawer :value="isShownScanStatusDrawer" fixed hide-overlay stateless right width="512">
    <v-list two-line flat disabled>
      <!-- Scan Name -->
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title class="title">
            {{ currentScan.name }}
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>

      <!-- Description -->
      <v-list-item v-if="currentScan.description">
        <v-list-item-content>
          <span class="overline text--secondary">Description</span>
          <div class="body-2">{{ currentScan.description }}</div>
        </v-list-item-content>
      </v-list-item>

      <!-- Target -->
      <v-list-item>
        <v-list-item-content>
          <span class="overline text--secondary">Target</span>
          <div class="body-2">{{ currentScan.target }}</div>
        </v-list-item-content>
      </v-list-item>

      <!-- Detector -->
      <v-list-item>
        <v-list-item-content>
          <span class="overline text--secondary">Detector</span>
          <div class="body-2">{{ currentScan.detection_module }} ({{ currentScan.detection_mode }})</div>
        </v-list-item-content>
      </v-list-item>

      <!-- If Periodic -->
      <v-list-item v-if="currentScan.rrule">
        <v-list-item-content>
          <span class="overline text--secondary">Periodic Scan</span>
          <div class="body-2">
            <v-icon small class="inline">loop</v-icon>
            {{ getNextDateTimeFromRRule(currentScan.rrule).format('[Every] dddd [at] ha') }}
          </div>
        </v-list-item-content>
      </v-list-item>

      <!-- If Scheduled -->
      <v-list-item v-if="getCurrentStatus() === 'Scheduled'">
        <v-list-item-content>
          <span class="overline text--secondary">Next Scan</span>
          <div class="body-2">
            <v-icon small class="inline">schedule</v-icon>
            {{ $helper.getLocalTime(currentScan.scheduled_at).format('h A [on] MMM DD') }} -
            {{
              $helper
                .getLocalTime(currentScan.scheduled_at)
                .clone()
                .add(currentScan.max_duration, 'hour')
                .format('h A, MMM DD')
            }}
          </div>
        </v-list-item-content>
      </v-list-item>

      <!-- If Scanning -->
      <v-list-item v-if="getCurrentStatus() === 'Scanning'">
        <v-list-item-content>
          <span class="overline text--secondary">Next Scan</span>
          <div class="body-2">
            <v-progress-circular indeterminate size="14" width="1" color="white" />
            {{ $helper.getLocalTime(currentScan.started_at).format('[Started] [at] h:mm A, MMM DD') }}
            ({{ getScanDurationInMinutes(currentScan.started_at) }} min.)
          </div>
        </v-list-item-content>
      </v-list-item>

      <!-- If Completed -->
      <v-list-item v-if="getCurrentStatus() === 'Completed'">
        <v-list-item-content>
          <span class="overline text--secondary">Scanned</span>
          <div class="body-2">
            <v-icon small class="inline">check_circle_outline</v-icon>
            {{ $helper.getLocalTime(currentScan.started_at).format('h:mm A, MMM DD') }} -
            {{ $helper.getLocalTime(currentScan.ended_at).format('h:mm A, MMM DD') }}
            ({{ getScanDurationInMinutes(currentScan.started_at, currentScan.ended_at) }} min.)
          </div>
        </v-list-item-content>
      </v-list-item>

      <!-- If Failed -->
      <v-list-item v-if="getCurrentStatus() === 'Failed'">
        <v-list-item-content>
          <span class="overline text--secondary">Error</span>
          <div class="body-2 error--text">
            <v-icon small color="error" class="inline">report_problem</v-icon>
            {{ currentScan.error_reason }}
          </div>
        </v-list-item-content>
      </v-list-item>
    </v-list>

    <!-- If Scheduled -->
    <div v-if="getCurrentStatus() === 'Scheduled'">
      <v-divider />
      <v-list-item>
        <v-list-item-content>
          <span class="overline text--secondary">Notice</span>
          <div class="body-2">
            Scan attempts will be coming from <b>{{ currentAudit.source_ip_address }}</b
            >.
          </div>
        </v-list-item-content>
      </v-list-item>
    </div>

    <!-- If Scanning -->
    <div v-if="getCurrentStatus() === 'Scanning'">
      <v-divider />
      <v-list-item>
        <v-list-item-content>
          <span class="overline text--secondary">Notice</span>
          <div class="body-2">
            Now scanning from <b>{{ currentAudit.source_ip_address }}</b
            >.
          </div>
        </v-list-item-content>
      </v-list-item>
    </div>

    <!-- If Completed -->
    <div v-if="getCurrentStatus() === 'Completed'">
      <v-divider />
      <v-progress-linear v-if="isScanStatusLoading" indeterminate></v-progress-linear>
      <v-subheader class="overline">Results</v-subheader>
      <v-list-item>
        <v-list-item-content class="my-0 py-0">
          <v-combobox
            v-model="selectedSeverities"
            :items="severities"
            chips
            label="Filter by severity"
            hide-details
            hide-selected
            multiple
            prepend-inner-icon="filter_list"
            dense
            outlined
            single-line
          >
            <template v-slot:selection="{ attrs, item, select, selected }">
              <v-chip
                v-bind="attrs"
                :input-value="selected"
                small
                close
                :color="severityColorPallet[item]"
                class="black--text"
                @click="select"
                @click:close="selectedSeverities.splice(selectedSeverities.indexOf(item), 1)"
              >
                {{ item }}
                <span v-if="selectedSeverities.length <= 3">({{ resultCount[item] }})</span>
              </v-chip>
            </template>
          </v-combobox>
        </v-list-item-content>
      </v-list-item>
      <v-list two-line dense flat>
        <v-list-item-group v-for="(result, key) in filteredResults" :key="key">
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>
                {{ result.name }}
              </v-list-item-title>
              <v-list-item-subtitle class="text--disabled">
                {{ result.description }}
              </v-list-item-subtitle>
            </v-list-item-content>

            <v-list-item-action>
              <v-chip x-small :color="severityColorPallet[result.severity]" class="black--text">
                {{ result.severity }}
              </v-chip>
            </v-list-item-action>
          </v-list-item>
          <v-divider></v-divider>
        </v-list-item-group>
      </v-list>
    </div>
  </v-navigation-drawer>
</template>

<script>
import moment from 'moment';
import { RRule } from 'rrule';
import colors from 'vuetify/lib/util/colors';
import { mapState, mapActions } from 'vuex';

export default {
  name: 'ScanStatusDrawer',

  watch: {
    currentScan: {
      handler(scan) {
        if (this.isShownScanStatusDrawer && this.getCurrentStatus() === 'Completed' && !scan.results) {
          // Load scan results when opened
          this.getScanStatus();
        }
      },
      deep: true,
    },
    isShownScanStatusDrawer: {
      handler(isOpen) {
        if (this.timer) {
          clearInterval(this.timer);
        }
        if (isOpen) {
          this.timer = setInterval(() => {
            if (['Scheduled', 'Scanning'].indexOf(this.getCurrentStatus()) >= 0) {
              this.getScanStatus();
            }
          }, this.reloadInterval);
        }
      },
    },
  },

  computed: {
    ...mapState(['currentAudit', 'currentScan', 'isShownScanStatusDrawer', '$http']),
    filteredResults() {
      const results = this.currentScan.results ? this.currentScan.results : [];
      return results.filter((result) => this.selectedSeverities.indexOf(result.severity) >= 0);
    },
  },

  methods: {
    ...mapActions(['setCurrentScan', 'updateScan']),
    async getScanStatus() {
      this.isScanStatusLoading = true;
      const resp = await this.$http.get(`/scan/${this.currentScan.uuid}/`).catch(() => {
        this.isError = true;
      });
      switch (resp.status) {
        case 200: {
          this.isScanStatusLoading = false;
          if (this.currentScan.uuid === resp.data.uuid) {
            this.setCurrentScan(resp.data);
            this.updateScan(resp.data);
            this.setResultCount(resp.data.results);
          }
          break;
        }
        default: {
          this.isError = true;
        }
      }
    },
    getCurrentStatus() {
      return this.$helper ? this.$helper.scanStatus(this.currentScan) : 'Unknown';
    },
    getNextDateTimeFromRRule(rruleString) {
      const rrule = RRule.fromString(rruleString);
      const recurrences = rrule.all((date, i) => i < 1);
      return moment(recurrences[0]);
    },
    getScanDurationInMinutes(start, end = undefined) {
      const utcOffset = moment().utcOffset();
      const endTime = end ? moment(end) : moment().subtract(utcOffset, 'minutes');
      return endTime.diff(moment(start), 'minutes');
    },
    setResultCount(results) {
      const count = {
        High: 0,
        Medium: 0,
        Low: 0,
        Info: 0,
      };
      results.map((result) => {
        count[result.severity] += 1;
        return undefined;
      });
      this.resultCount = count;
    },
  },

  data: () => ({
    isScanStatusLoading: false,
    selectedSeverities: ['High', 'Medium'],
    severities: ['High', 'Medium', 'Low', 'Info'],
    reloadInterval: Number(process.env.VUE_APP_SCAN_RELOAD_INTERVAL),
    resultCount: {
      High: 0,
      Medium: 0,
      Low: 0,
      Info: 0,
    },
    severityColorPallet: {
      High: colors.amber.darken1,
      Medium: colors.amber.lighten2,
      Low: colors.amber.lighten4,
      Info: colors.grey.lighten2,
    },
    timer: null,
  }),
};
</script>
