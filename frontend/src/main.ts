/**
 * Main Vue application entry point.
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'

// PrimeVue components
import Button from 'primevue/button'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import ProgressSpinner from 'primevue/progressspinner'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import Skeleton from 'primevue/skeleton'
import Tag from 'primevue/tag'
import TabMenu from 'primevue/tabmenu'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Panel from 'primevue/panel'
import Chip from 'primevue/chip'

// PrimeVue styles (Aura dark theme)
import 'primevue/resources/themes/aura-dark-noir/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'

// Design system (must be after PrimeVue to override)
import '@/assets/css/index.css'

// ECharts
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart, RadarChart, HeatmapChart, ScatterChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  RadarComponent,
  VisualMapComponent
} from 'echarts/components'

// App components
import App from './App.vue'
import router from './router'

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  RadarChart,
  HeatmapChart,
  ScatterChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  RadarComponent,
  VisualMapComponent
])

// Create Vue app
const app = createApp(App)

// Install plugins
app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  ripple: true,
})
app.use(ToastService)

// Register global components
app.component('Button', Button)
app.component('Card', Card)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Dropdown', Dropdown)
app.component('InputText', InputText)
app.component('ProgressSpinner', ProgressSpinner)
app.component('Toast', Toast)
app.component('Skeleton', Skeleton)
app.component('Tag', Tag)
app.component('TabMenu', TabMenu)
app.component('TabView', TabView)
app.component('TabPanel', TabPanel)
app.component('Panel', Panel)
app.component('Chip', Chip)
app.component('VChart', ECharts)

// Mount app
app.mount('#app')
