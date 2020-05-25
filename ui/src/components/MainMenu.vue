<template>
  <div>
    <v-menu>
      <template v-slot:activator="{ on }">
        <v-btn icon v-on="on">
          <v-icon>menu</v-icon>
        </v-btn>
      </template>

      <v-list dense>
        <v-list-item @click="isShownIntegrationSlackDialog = true">
          <v-list-item-icon>
            <v-icon>swap_horiz</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Slack Integration</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item>
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
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import IntegrationSlackDialog from '@/components/IntegrationSlackDialog.vue';

export default {
  name: 'MainMenu',

  components: {
    IntegrationSlackDialog,
  },

  computed: {
    //
  },

  methods: {
    ...mapActions(['forgetToken']),
    conrifmLogout() {
      if (window.confirm('Are you sure you want to log out?')) {
        this.forgetToken();
        window.location.reload();
      }
    },
  },

  data: () => ({
    isShownIntegrationSlackDialog: false,
  }),
};
</script>
