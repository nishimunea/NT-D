import Vue from 'vue';
import moment from 'moment';

export default {
  install() {
    const helper = {
      getLocalTime(utcDateTimeString) {
        return moment.utc(utcDateTimeString).local();
      },
      scanStatus(scan) {
        let status = 'Unknown';
        if (scan.scheduled_at) {
          status = 'Scheduled';
          if (scan.started_at) {
            status = 'Scanning';
          }
        } else if (scan.error_reason.length > 0) {
          status = 'Failed';
        } else if (scan.ended_at) {
          status = 'Completed';
        } else if (scan.rrule) {
          status = 'Scheduled';
        } else {
          status = 'Unscheduled';
        }
        return status;
      },
    };
    Vue.prototype.$helper = helper;
  },
};
