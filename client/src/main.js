import Vue from 'vue'
import App from './App.vue'

import VueNesCss from 'vuenes.css'

import axios from 'axios'


Vue.prototype.$axios = axios;
Vue.use(VueNesCss)

Vue.config.productionTip = false

new Vue({
  render: h => h(App),
}).$mount('#app')
