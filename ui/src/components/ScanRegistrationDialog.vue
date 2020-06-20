<template>
  <v-dialog v-model="isShown" max-width="500pt">
    <v-card>
      <v-card-title>
        <span class="headline">New Scan</span>
      </v-card-title>
      <v-form ref="form" v-model="isFormValid" @submit.prevent="createScan">
        <v-card-text>
          <v-alert v-if="errorMessage" type="error" icon="error" dense text class="mt-3 mb-0">
            {{ errorMessage }}
          </v-alert>
          <v-container class="pb-0">
            <v-row dense>
              <v-col cols="12" sm="8">
                <v-select
                  v-model="selected.detection_module"
                  outlined
                  dense
                  label="Detector"
                  :items="detectorCandidates"
                  :hint="selected.detection_module ? selected.detection_module.description : ''"
                  menu-props="auto"
                  placeholder="Choose"
                  autofocus
                ></v-select>
              </v-col>
              <v-col cols="12" sm="4">
                <v-select
                  v-model="selected.detection_mode"
                  outlined
                  dense
                  label="Detection Mode"
                  :items="selected.detection_module ? selected.detection_module.supported_mode : []"
                  menu-props="auto"
                  class="capitalize"
                ></v-select>
              </v-col>
            </v-row>

            <v-row dense>
              <v-col cols="12">
                <v-text-field
                  v-model="selected.target"
                  dense
                  :rules="[validateMinLength]"
                  :label="`Scan Target ${
                    selected.detection_module ? '(' + selected.detection_module.target_type + ')' : ''
                  }`"
                  :placeholder="
                    selected.detection_module ? targetPlaceholder[selected.detection_module.target_type] : ' '
                  "
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" sm="4">
                <v-text-field
                  v-model="selected.name"
                  dense
                  :counter="maxInputLength"
                  :rules="[validateMinLength, validateMaxLength]"
                  label="Scan Name"
                  :placeholder="`${selected.detection_module ? selected.detection_module.name : ''}${
                    selected.detection_mode ? ` ${selected.detection_mode} scan` : ''
                  }`"
                />
              </v-col>
              <v-col cols="12" sm="8">
                <v-text-field
                  v-model="selected.description"
                  dense
                  :counter="maxInputLength"
                  :rules="[validateMaxLength]"
                  label="Description (Optional)"
                />
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="close">Cancel</v-btn>
          <v-btn text color="primary" :disabled="!isFormValid" @click="createScan">Create</v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'ScanRegistrationDialog',

  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },

  watch: {
    value(isOpen) {
      if (isOpen) {
        this.errorMessage = '';
        this.selected = {
          name: '',
          description: '',
        };
        if (this.$refs.form) {
          this.$refs.form.reset();
        }
      } else {
        this.selected = {};
      }
    },
    'selected.detection_module': function watchSelectedDetectionModule(detectionModule) {
      if (detectionModule) {
        const mode = detectionModule.supported_mode[0];
        this.selected.detection_mode = mode;
      }
    },
  },

  computed: {
    ...mapState(['currentAuditUUID', '$http']),
    isShown: {
      get() {
        return this.value;
      },
      set(value) {
        this.$emit('input', value);
      },
    },
    detectorCandidates() {
      return this.detectors.map((detector) => {
        const text = `${detector.name}, ${detector.version} (${detector.stage})`;
        return { text, value: detector };
      });
    },
  },

  methods: {
    ...mapActions(['setSnackbar']),
    validateMinLength(value) {
      const error = 'Must not be empty';
      return (value || '').length !== 0 || error;
    },
    validateMaxLength(value) {
      const error = `Must be equal or less than ${this.maxInputLength} characters`;
      return (value || '').length <= this.maxInputLength || error;
    },
    close() {
      this.isShown = false;
    },
    async createScan() {
      const body = { ...this.selected };
      body.detection_module = this.selected.detection_module.module;
      const resp = await this.$http.post(`/audit/${this.currentAuditUUID}/scan/`, body).catch(() => {
        this.errorMessage = 'Something went wrong while creating new scan';
      });
      switch (resp.status) {
        case 200: {
          this.setSnackbar({ message: 'Created new scan successfully!', isError: false });
          this.$emit('updated', resp.data);
          this.close();
          break;
        }
        default: {
          this.errorMessage = resp.data.message;
        }
      }
    },
    async getDetectors() {
      const resp = await this.$http.get('/detector/').catch(() => {
        this.errorMessage = 'Something went wrong while loading detector info';
      });
      switch (resp.status) {
        case 200: {
          this.detectors = resp.data;
          break;
        }
        default: {
          this.errorMessage = resp.data.message;
        }
      }
    },
  },

  data: () => ({
    isFormValid: false,
    maxInputLength: Number(process.env.VUE_APP_MAX_TEXT_INPUT_LENGTH),
    selected: {},
    detectors: [],
    targetPlaceholder: {
      Host: 'IPv4 address or FQDN',
      URL: 'http(s)://',
    },
    errorMessage: '',
  }),

  mounted() {
    this.getDetectors();
  },
};
</script>
<style scoped>
.capitalize {
  text-transform: capitalize;
}
</style>
