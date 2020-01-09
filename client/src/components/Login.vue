<template>
    <div class="nes-container with-title" id="app-login" v-if="!isLoggedIn">
        <p class="title">{{ component_title }}</p>
        <div class="nes-field">
            <input type="text" id="title" class="nes-input" placeholder="User Name" v-model="username">
        </div>
        <div class="nes-field">
            <input type="password" id="title" class="nes-input" placeholder="Password" v-model="password">
        </div>
        <button type="button" class="nes-btn is-success" v-on:click="login">Login</button>
    </div>
</template>

<script>
 export default {
     name: 'Login',
     props: {
         component_title: String
     },
     data: function() {
         return {
             token: '',
             isLoggedIn: localStorage.token != undefined && localStorage.token != '',
             username: '',
             password: ''
         }
     },
     methods: {
         login: function () {
             var formData = new FormData();
             formData.append('username', this.username);
             formData.append('password', this.password);

             this.$axios({
                 method: 'post',
                 url: 'http://localhost:8000/token',
                 data: formData,
                 headers:{
                     'Content-Type': 'application/x-wwwf-orm-urlencoded'
                 }
             }).then(response => {
                 /* this.info = response.data.bpi */
                 /* console.log(response) */
                 localStorage.token =  response.data.access_token
                 this.isLoggedIn = true
                 this.$root.$emit('logged_in')
             }).catch(error => {
                 /* console.log(error) */
                 this.errored = true
                 alert("Error man!!!" + error)
             }).finally(() => this.loading = false)

         }
     }
 }
</script>
