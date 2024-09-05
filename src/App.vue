<script setup>
import {RouterView} from 'vue-router'
import MainNavbar from "@/components/MainNavbar.vue";
</script>

<template>
  <div>
    <MainNavbar/>
    <div class="container py-3">
      <RouterView/>
    </div>
  </div>
</template>
