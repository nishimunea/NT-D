<template>
  <v-content>
    <v-container class="fill-height">
      <v-row align="center" justify="center">
        <v-col class="col-3" />
        <v-col>
          <v-card outlined>
            <v-card-title class="display-1 font-weight-black">NT-D</v-card-title>
            <v-card-subtitle class="subtitle-1">Network Threat Detector</v-card-subtitle>
            <div v-if="status === 0">
              <v-progress-linear indeterminate background-color="grey darken-4" color="grey darken-3" />
              <v-card-text>Loading...</v-card-text>
            </div>
            <div v-else-if="status === 401">
              <v-divider />
              <v-card-title>Administrator Login</v-card-title>
              <v-card-text>
                <v-alert :value="errorMessage.length > 0" type="error" icon="error" dense text dismissible>
                  {{ errorMessage }}
                </v-alert>
                <v-text-field
                  v-model="password"
                  name="password"
                  label="Master Password"
                  type="password"
                  prepend-icon="lock"
                  v-on:keyup.enter="doAuthenticate"
                />
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn @click="doAuthenticate">Login</v-btn>
              </v-card-actions>
            </div>
            <div v-else-if="status === 403">
              <v-card-text>
                <v-alert type="error" icon="error" dense text>Access is not allowed from your IP address</v-alert>
              </v-card-text>
            </div>
            <div v-else-if="status === 404">
              <v-card-text>
                <v-alert type="error" icon="error" dense text>Audit not found</v-alert>
              </v-card-text>
            </div>
            <div v-else>
              <v-card-text>
                <v-alert type="warning" icon="warning" dense text>Unknown error</v-alert>
              </v-card-text>
            </div>
          </v-card>
        </v-col>
        <v-col class="col-3" />
      </v-row>
    </v-container>
  </v-content>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'Entrance',

  computed: {
    ...mapState(['status', '$http']),
  },

  methods: {
    ...mapActions(['setStatus', 'setToken']),
    async doAuthenticate() {
      this.errorMessage = '';
      const resp = await this.$http.post('/session/', { password: this.password }).catch(() => {
        this.setStatus(500);
      });
      switch (resp.status) {
        case 200:
          this.setToken(resp.data.token);
          window.location.reload();
          break;
        case 401:
          this.errorMessage = resp.data.message;
          this.setStatus(401);
          break;
        default:
          this.setStatus(resp.status);
      }
    },
  },

  data: () => ({
    password: '',
    errorMessage: '',
  }),
};
</script>
