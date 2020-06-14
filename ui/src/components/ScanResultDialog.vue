<template>
  <v-dialog v-model="isShown" max-width="500pt">
    <v-card>
      <v-card-title class="headline card-title-ellipsis">
        {{ currentResult.name }}
      </v-card-title>
      <v-card-text>
        <pre>{{ currentResult.description }}</pre>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="close">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: 'ScanResultDialog',

  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },

  computed: {
    ...mapState(['currentResult']),
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
    close() {
      this.isShown = false;
    },
  },

  data: () => ({
    //
  }),
};
</script>

<style scoped>
pre {
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
