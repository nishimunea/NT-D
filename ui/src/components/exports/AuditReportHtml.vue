<template>
  <html lang="en" class="h-100">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
      <link
        rel="stylesheet"
        href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css"
        crossorigin="anonymous"
      />
      <title>{{ audit.name }}</title>
    </head>
    <body class="d-flex flex-column h-100">
      <div class="container">
        <h1 class="mt-5 text-truncate">{{ audit.name }}</h1>
        <p class="font-weight-light">{{ audit.description }}</p>
        <ul class="list-inline">
          <li class="list-inline-item"><b>High</b> {{ resultCount.High }}</li>
          <li class="list-inline-item"><b>Medium</b> {{ resultCount.Medium }}</li>
          <li class="list-inline-item"><b>Low</b> {{ resultCount.Low }}</li>
          <li class="list-inline-item"><b>Info</b> {{ resultCount.Info }}</li>
        </ul>
        <hr class="my-4" />
        <div v-for="(scan, index) in getCompletedScans(audit.scans)" :key="index" class="mb-5">
          <h3 class="text-truncate">{{ index + 1 }}. {{ scan.name }}</h3>
          <p class="font-weight-light">{{ scan.description }}</p>
          <div class="row">
            <div class="col-md-4">
              <div class="mb-4">
                <b>Target</b>
                <p class="text-truncate">{{ scan.target }}</p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="mb-4">
                <b>Detector</b>
                <p class="text-truncate">{{ scan.detection_module }} ({{ scan.detection_mode }})</p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="mb-4">
                <b>Scan Date (Duration)</b>
                <p class="text-truncate">
                  {{ $helper.getLocalTime(scan.started_at).format('YYYY/MM/DD hh:mm:ss') }}
                  ({{ getScanDurationInMinutes(scan.started_at, scan.ended_at) }} min.)
                </p>
              </div>
            </div>
          </div>
          <table class="table table-sm table-bordered">
            <thead class="thead-light">
              <tr>
                <th scope="col">Severity</th>
                <th scope="col">Finding</th>
                <th scope="col">Details</th>
                <th scope="col">Host</th>
                <th scope="col">Port</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, j) in scan.results" :key="j">
                <td>{{ result.severity }}</td>
                <td>{{ result.name }}</td>
                <td>{{ result.description }}</td>
                <td>{{ result.host }}</td>
                <td>{{ result.port }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <footer class="footer mt-auto pb-3 mt-0">
        <div class="container text-center mt-0">
          <p class="text-muted">Powered by {{ appName }}</p>
        </div>
      </footer>
    </body>
  </html>
</template>
<script>
import { mapState, mapActions } from 'vuex';
import moment from 'moment';

export default {
  name: 'AuditReportHtml',

  computed: {
    ...mapState(['currentAuditUUID', '$http']),
  },

  methods: {
    ...mapActions(['setSnackbar']),
    async getCurrentAudit() {
      const resp = await this.$http.get(`/audit/${this.currentAuditUUID}/?include_results=true`).catch(() => {
        this.setSnackbar({ message: 'Something went wrong while generating audit report.', isError: true });
      });
      switch (resp.status) {
        case 200: {
          this.audit = resp.data;
          break;
        }
        default: {
          this.setSnackbar({ message: 'Something went wrong while generating audit report.', isError: true });
        }
      }
    },
    getCompletedScans(scans) {
      return scans.filter((scan) => this.$helper.scanStatus(scan) === 'Completed');
    },
    getScanDurationInMinutes(start, end) {
      return moment(end).diff(moment(start), 'minutes');
    },
    setResultCount() {
      const count = {
        High: 0,
        Medium: 0,
        Low: 0,
        Info: 0,
      };
      this.audit.scans.map((scan) => {
        if (this.$helper.scanStatus(scan) === 'Completed') {
          scan.results.map((result) => {
            count[result.severity] += 1;
            return undefined;
          });
        }
        return undefined;
      });
      this.resultCount = count;
    },
  },

  data: () => ({
    audit: { scans: [] },
    appName: process.env.VUE_APP_TITLE,
    resultCount: {
      High: 0,
      Medium: 0,
      Low: 0,
      Info: 0,
    },
  }),

  async mounted() {
    await this.getCurrentAudit();
    this.setResultCount();
    this.$nextTick(() => {
      this.$emit('loaded');
    });
  },
};
</script>
