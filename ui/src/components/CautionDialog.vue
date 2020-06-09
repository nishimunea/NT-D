<template>
  <v-dialog v-model="isShown" persistent max-width="500pt">
    <v-card>
      <v-card-title>
        <span class="headline">
          <v-icon class="pb-1 mr-1">report_problem</v-icon>
          <span>Caution</span>
        </span>
      </v-card-title>
      <v-card-text class="pb-0" v-html="message"></v-card-text>
      <v-card-actions class="pt-0">
        <v-spacer></v-spacer>
        <v-btn text color="primary" @click="accept">Accept</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'CautionDialog',

  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },

  computed: {
    ...mapState(['currentAudit']),
    isShown: {
      get() {
        return this.value;
      },
      set(value) {
        this.$emit('input', value);
      },
    },
    message() {
      return `<p>We impose restrictions on your use of this tool. You are prohibited from attempting to interfere with any networks or hosts you are not authorized to access. You must first secure written authorization from owner of your target before initiating any scanning. It is to be understood that we shall not be held responsible for any damage incurred as a result of scanning by this tool.</p><p>The scanning from this tool will be coming from <b><u>${this.currentAudit.source_ip_address}</u></b>. Prior to scanning, please add the source IP address to the whitelists in your access restrictions (e.g. firewall rules) or intrusion monitoring systems (e.g. IDS/IPS).</p>`;
    },
  },

  methods: {
    ...mapActions(['setIsPolicyAccepted']),
    accept() {
      this.setIsPolicyAccepted(true);
      this.isShown = false;
    },
  },

  data: () => ({
    //
  }),
};
</script>
