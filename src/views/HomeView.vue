<script setup>
import {useAxios} from '@vueuse/integrations/useAxios'
import axiosInstance from "@/libs/axios.js";
import {ref, watch} from "vue";
import {Line} from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale, PointElement, Filler
} from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement, Filler);

const categorySelected = ref("-")
const itemSelected = ref("-")
const timeframeSelected = ref("D")
const n = ref(1)

const chartData = ref(null)

const {data: categories} = useAxios('categories', {method: 'GET'}, axiosInstance, {
  immediate: true,
  initialData: {categories: []}
});
const {data: items, execute: fetchItems} = useAxios('items', {method: 'GET'}, axiosInstance, {
  immediate: false,
  initialData: {items: []}
});

watch(categorySelected, async (newCategory) => {
  if (newCategory === "-") {
    itemSelected.value = "-"
    return
  }

  fetchItems({params: {category: newCategory}})
})

const {execute: predict} = useAxios('predict', {method: 'POST'}, axiosInstance, {
  immediate: false
});

const handlePredict = async () => {
  const result = await predict({
    data: {
      kategori: categorySelected.value,
      "nama_barang": itemSelected.value,
      timeframe: timeframeSelected.value,
      "n_predictions": n.value
    }
  })

  chartData.value = {
    labels: result.data.value.map(p => p.ds),
    datasets: [
      {
        label: 'Prediction',
        data: result.data.value.map(p => p.yhat),
        borderColor: 'blue',
        backgroundColor: 'rgba(0, 0, 255, 0.2)',
        fill: true,
        tension: 0.3
      },
      {
        label: 'Lower Bound',
        data: result.data.value.map(p => p.yhat_lower),
        borderColor: 'red',
        backgroundColor: 'rgba(255, 0, 0, 0.2)',
        borderDash: [10, 5],
        fill: false,
        tension: 0.3
      },
      {
        label: 'Upper Bound',
        data: result.data.value.map(p => p.yhat_upper),
        borderColor: 'green',
        backgroundColor: 'rgba(0, 255, 0, 0.2)',
        borderDash: [10, 5],
        fill: false,
        tension: 0.3
      }
    ]
  }
}
</script>

<template>
  <main>
    <form @submit.prevent="handlePredict">
      <div class="mb-3">
        <label for="kategori" class="form-label">Kategori</label>
        <select class="form-select" id="kategori" name="kategori" v-model="categorySelected">
          <option selected value="-">-</option>
          <option v-for="category in categories.categories" :key="category" :value="category">{{ category }}</option>
        </select>
      </div>
      <div class="mb-3">
        <label for="nama" class="form-label">Nama Barang</label>
        <select class="form-select" id="nama" name="nama" v-model="itemSelected">
          <option selected value="-">-</option>
          <option v-for="item in items.items" :key="item" :value="item">{{ item }}</option>
        </select>
      </div>
      <div class="mb-3 row">
        <div class="col">
          <label for="timeframe" class="form-label">Timeframe</label>
          <select class="form-select" id="timeframe" name="timeframe" v-model="timeframeSelected">
            <option value="D">Hari</option>
            <option value="M">Bulan</option>
          </select>
        </div>
        <div class="col">
          <label for="n" class="form-label">Jenjang Waktu</label>
          <input type="number" id="n" name="n" class="form-control" v-model="n">
        </div>
      </div>
      <button type="submit" class="btn btn-primary">Predict</button>
    </form>

    <div v-if="chartData">
      <Line :data="chartData" :options="{ responsive: true }"></Line>
    </div>
  </main>
</template>
