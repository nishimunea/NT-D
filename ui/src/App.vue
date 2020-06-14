<template>
  <v-app>
    <Entrance v-if="status !== 200" />
    <Home v-show="status === 200" />
  </v-app>
</template>

<script>
import axios from 'axios';
import { mapState, mapActions } from 'vuex';
import Entrance from '@/components/Entrance.vue';
import Home from '@/components/Home.vue';

export default {
  name: 'App',

  components: {
    Entrance,
    Home,
  },

  computed: {
    ...mapState(['apiEndpoint', 'apiTimeout', 'status', 'token']),
  },

  methods: {
    ...mapActions(['setCurrentAuditUUID', 'setCurrentScanUUID', 'setHTTPClient', 'setToken', 'forgetToken']),
    createHTTPClient(token) {
      const httpClient = axios.create({
        baseURL: this.apiEndpoint,
        timeout: this.apiTimeout,
        headers: { Authorization: `Bearer ${token}` },
        validateStatus: () => true,
      });
      httpClient.interceptors.response.use(
        (response) => {
          if (response.status === 401) {
            // POST `/session/` allows to handle unauthorized errors by request initiators
            const responseURL = new URL(response.request.responseURL);
            const responsePath = responseURL.pathname;
            if (responsePath === '/session/' && response.config.method === 'post') {
              return response;
            }
            // Otherwise remove invalid token and reload
            this.forgetToken();
            // If re-auth endpoint is specified in the expired token
            if (response.data.reauth_endpoint) {
              window.location = response.data.reauth_endpoint;
            }
          }
          return response;
        },
        (error) => Promise.reject(error)
      );
      return httpClient;
    },
  },

  data: () => ({
    //
  }),

  created() {
    const qs = window.location.search.substring(1).split('&');
    // If access token is given through the 2nd query parameter
    if (qs.length >= 2) {
      // Store the token to the browser's local storage
      this.setToken(qs[1]);
      // Reload the document here
      window.location.search = String(qs[0]);
    }
    // Set target audit UUID given through the 1st query parameter
    if (qs[0].length > 0) {
      const uuid = qs[0].toLowerCase();
      const auditUUID = uuid.slice(0, 24) + '0'.repeat(8);
      this.setCurrentAuditUUID(auditUUID);
      // Set target scan UUID if scan UUID is given
      if (uuid.slice(24, 32) !== '0'.repeat(8)) {
        this.setCurrentScanUUID(uuid);
      }
    }

    // Create HTTP client (axios) with the access token
    this.setHTTPClient(this.createHTTPClient(this.token));
  },
};
</script>
<style>
.card-title-ellipsis {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  display: block;
}

.elipsis {
  display: inline-block;
  vertical-align: inherit;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}
.row td {
  cursor: pointer;
}

.v-icon.inline {
  padding-bottom: 2pt;
}

input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
  border: 0px solid transparent;
  -webkit-text-fill-color: white;
  -webkit-box-shadow: 0 0 0 1000px #1e1e1e inset;
  transition: background-color 5000s ease-in-out 0s;
}
</style>
