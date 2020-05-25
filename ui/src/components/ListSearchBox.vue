<template>
  <v-menu
    v-model="isShown"
    :close-on-content-click="false"
    :close-delay="50"
    :min-width="400"
    :max-width="400"
    :open-on-hover="true"
    :nudge-bottom="3"
    bottom
    offset-y
  >
    <template v-slot:activator="{ on }">
      <v-btn v-on="on"><v-icon icon>search</v-icon></v-btn>
    </template>
    <v-card outlined>
      <v-card-text>
        <v-text-field
          v-model="search"
          append-icon="search"
          label="Search"
          dense
          single-line
          hide-details
          @keyup.enter="isShown = false"
        />
      </v-card-text>
    </v-card>
  </v-menu>
</template>

<script>
export default {
  name: 'ListSearchBox',

  props: {
    value: {
      type: String,
      required: true,
    },
  },

  computed: {
    search: {
      get() {
        return this.value;
      },
      set(value) {
        this.$emit('input', value);
      },
    },
  },

  methods: {
    //
  },

  data: () => ({
    isShown: false,
  }),
};
</script>
