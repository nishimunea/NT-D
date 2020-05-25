<template>
  <v-dialog v-model="isShown" max-width="500pt">
    <v-card>
      <v-card-title>
        <span class="headline">Slack Integration</span>
      </v-card-title>
      <v-form ref="form" v-model="isFormValid" @submit.prevent="setIntegration">
        <v-card-text>
          <v-alert v-if="errorMessage" type="error" icon="error" dense text class="mt-3 mb-0">
            {{ errorMessage }}
          </v-alert>
          <v-container class="pb-0">
            <v-row dense>
              <v-col cols="9">
                <v-text-field
                  v-model="selected.url"
                  dense
                  :rules="[validateMinLength]"
                  label="Webhook URL"
                  placeholder="https://hooks.slack.com/..."
                  autofocus
                />
              </v-col>
              <v-col cols="3">
                <v-select :items="messageLevels" label="Message Level" dense hide-details />
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions class="pt-0">
          <v-spacer></v-spacer>
          <v-btn text @click="close">Cancel</v-btn>
          <v-btn text color="primary" :disabled="!isFormValid" @click="setIntegration">Set</v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'IntegrationSlackDialog',

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
  },

  computed: {
    ...mapState(['$http']),
    isShown: {
      get() {
        return this.value;
      },
      set(value) {
        this.$emit('input', value);
      },
    },
  },

  methods: {
    ...mapActions(['setAudit', 'setSnackbar']),
    close() {
      this.isShown = false;
    },
    validateMinLength(value) {
      const error = 'Must not be empty';
      return (value || '').length !== 0 || error;
    },
    validateMaxLength(value) {
      const error = `Must be equal or less than ${this.maxInputLength} characters`;
      return (value || '').length <= this.maxInputLength || error;
    },
    async setIntegration() {
      alert('Under construction');
      this.isShown = false;
    },
  },

  data: () => ({
    isFormValid: false,
    maxInputLength: Number(process.env.VUE_APP_MAX_TEXT_INPUT_LENGTH),
    messageLevels: ['normal', 'verbose'],
    selected: {},
    errorMessage: '',
  }),
};
</script>
