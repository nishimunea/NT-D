<template>
  <v-dialog v-model="isShown" max-width="500pt">
    <v-card>
      <v-card-title>
        <span class="headline">New Audit</span>
      </v-card-title>
      <v-form ref="form" v-model="isFormValid" @submit.prevent="createAudit">
        <v-card-text>
          <v-alert v-if="errorMessage" type="error" icon="error" dense text class="mt-3 mb-0">
            {{ errorMessage }}
          </v-alert>
          <v-container class="pb-0">
            <v-row dense>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="selected.name"
                  dense
                  :counter="maxInputLength"
                  :rules="[validateMaxLength, validateMinLength]"
                  label="Audit Name"
                  autofocus
                />
              </v-col>
            </v-row>
            <v-row dense>
              <v-col cols="12">
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
          <v-btn text color="primary" :disabled="!isFormValid" @click="createAudit">Create</v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'AuditRegistrationDialog',

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
    async createAudit() {
      const resp = await this.$http.post('/audit/', this.selected).catch(() => {
        this.errorMessage = 'Something went wrong while creating new audit';
      });
      switch (resp.status) {
        case 200: {
          this.setSnackbar({ message: 'Created new audit successfully!', isError: false });
          this.$emit('updated'); // Reload audit list
          this.close();
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
    errorMessage: '',
  }),
};
</script>
