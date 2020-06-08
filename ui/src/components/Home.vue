<template>
  <div @click.stop="closeDrawers" style="height: 100%;">
    <v-app-bar app dense>
      <v-toolbar-title class="headline font-weight-bold">NT-D</v-toolbar-title>
      <v-spacer />
      <ScanMenu v-if="currentAuditUUID" />
    </v-app-bar>
    <v-content>
      <v-container class="fill-height">
        <v-row class="my-2">
          <div v-if="currentAuditUUID">
            <v-col>
              <h1 class="headline font-weight-bold text--primary">
                {{ audit.name }}
              </h1>
              <h2 class="caption text--secondary">{{ audit.description }}</h2>
            </v-col>
          </div>
          <div v-else>
            <v-col>
              <h1 class="headline font-weight-bold"></h1>
            </v-col>
          </div>
        </v-row>
        <v-row>
          <v-col>
            <div v-if="currentAuditUUID">
              <ScanList />
            </div>
            <div v-else>
              <AuditList />
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-content>
    <v-snackbar v-model="isShownSnackbar" bottom color="white" :timeout="2500">
      <span :class="[currentSnackbar.isError ? 'error--text' : 'secondary--text']">
        {{ currentSnackbar.message }}
      </span>
    </v-snackbar>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import AuditList from '@/components/AuditList.vue';
import ScanMenu from '@/components/ScanMenu.vue';
import ScanList from '@/components/ScanList.vue';

export default {
  name: 'Home',

  components: {
    AuditList,
    ScanList,
    ScanMenu,
  },

  watch: {
    snackbar: {
      handler(content) {
        if (content.message) {
          this.isShownSnackbar = true;
          this.currentSnackbar = { ...content };
          this.setSnackbar({ message: '', isError: false });
        }
      },
      deep: true,
    },
  },

  computed: {
    ...mapState(['audit', 'currentAuditUUID', 'snackbar', '$http']),
  },

  methods: {
    ...mapActions(['setIsShownScanStatusDrawer', 'setSnackbar']),
    closeDrawers() {
      this.setIsShownScanStatusDrawer(false);
    },
  },

  data: () => ({
    isShownSnackbar: false,
    currentSnackbar: {},
  }),
};
</script>
