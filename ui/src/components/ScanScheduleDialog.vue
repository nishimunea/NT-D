<template>
  <v-dialog v-model="isShown" max-width="500pt">
    <v-card>
      <v-card-title>
        <span class="headline card-title-ellipsis">Scan Schedule ({{ currentScan.name }})</span>
      </v-card-title>
      <v-card-text class="pb-0">
        <v-container class="pb-0">
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-select
                v-model="selected.scheduledDate"
                outlined
                dense
                label="Start Date"
                :items="startDateCandidates"
                menu-props="auto"
                autofocus
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-select
                v-model="selected.scheduledTime"
                outlined
                dense
                label="Start Time"
                :items="startTimeCandidates"
                menu-props="auto"
              ></v-select>
            </v-col>
          </v-row>
          <v-row dense>
            <v-col cols="12" sm="6" md="4">
              <v-select
                v-model="selected.maxDuration"
                outlined
                dense
                label="Max Duration (in Hour)"
                :items="maxDurationCandidates"
                menu-props="auto"
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" class="mt-2">
              Terminate scan at <b>{{ terminateAt.format('h A, MMM DD') }}</b> if beyond
            </v-col>
          </v-row>
          <v-row dense>
            <v-col cols="12">
              <v-checkbox
                v-model="selected.isPeriodic"
                :label="startAt.format('[Repeat] [every] dddd [at] h A')"
                class="mt-0 pt-0"
              />
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="close">Cancel</v-btn>
        <v-btn text color="primary" @click="setSchedule">Set</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import moment from 'moment';
import { RRule } from 'rrule';
import { mapState, mapActions } from 'vuex';

export default {
  name: 'ScanScheduleDialog',

  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },

  watch: {
    value(isOpen) {
      if (isOpen) {
        // Set initial form value when opened
        this.selected = {
          scheduledDate: moment().format('YYYY-MM-DD'),
          scheduledTime: moment().format('HH:00:00'),
          maxDuration: 24,
          isPeriodic: false,
        };
      } else {
        this.selected = {};
      }
    },
  },

  computed: {
    ...mapState(['currentScan', '$http']),
    isShown: {
      get() {
        return this.value;
      },
      set(value) {
        this.$emit('input', value);
      },
    },
    startDateCandidates() {
      const candidates = [];
      const day = moment(); // Today
      for (let i = 0; i < this.schedulableDateCandidateCount; i += 1) {
        candidates.push({ value: day.format('YYYY-MM-DD'), text: day.format('MMM DD (ddd)') });
        day.add(1, 'day');
      }
      candidates[0].text += ', Today';
      return candidates;
    },
    startTimeCandidates() {
      const candidates = [];
      const time = moment().hour(0).minutes(0).seconds(0);
      for (let i = 0; i < this.schedulableTimeCandidateCount; i += 1) {
        candidates.push({ value: time.format('HH:00:00'), text: time.format('h A') });
        time.add(1, 'hour');
      }
      return candidates;
    },
    maxDurationCandidates() {
      const candidates = Array.from(Array(this.schedulableMaxDurationHour), (d, i) => i);
      candidates.splice(0, this.schedulableMinDurationHour);
      return candidates;
    },
    startAt() {
      return moment(`${this.selected.scheduledDate} ${this.selected.scheduledTime}`, 'YYYY-MM-DD HH-mm-ss');
    },
    terminateAt() {
      return this.startAt.clone().add(this.selected.maxDuration, 'hour');
    },
  },

  methods: {
    ...mapActions(['updateScan', 'setSnackbar']),
    close() {
      this.isShown = false;
    },
    async setSchedule() {
      const utcOffset = moment().utcOffset();
      const startAtUtc = this.startAt.subtract(utcOffset, 'minutes');
      const schedule = {
        scheduled_at: startAtUtc.format('YYYY-MM-DDTHH:mm:ss'),
        max_duration: this.selected.maxDuration,
      };
      if (this.selected.isPeriodic) {
        const rrule = new RRule({
          freq: RRule.WEEKLY,
          byweekday: (startAtUtc.day() + 6) % 7, // Monday == 0 in RRule
          byhour: [startAtUtc.format('HH')],
        });
        schedule.rrule = rrule.toString();
      }
      const resp = await this.$http.post(`/scan/${this.currentScan.uuid}/schedule/`, schedule).catch(() => {
        this.setSnackbar({ message: 'Something went wrong while setting the schedule.', isError: true });
      });
      switch (resp.status) {
        case 200: {
          this.setSnackbar({ message: 'Set the schedule successfully!', isError: false });
          this.updateScan(resp.data);
          break;
        }
        default: {
          this.setSnackbar({ message: `Failed to set the schedule with response code: ${resp.status}`, isError: true });
        }
      }
      this.close();
    },
  },

  data: () => ({
    schedulableDateCandidateCount: 7,
    schedulableTimeCandidateCount: 24,
    schedulableMaxDurationHour: 25,
    schedulableMinDurationHour: 3,
    selected: {},
  }),
};
</script>
<style scoped>
.card-title-ellipsis {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  display: block;
}
</style>
