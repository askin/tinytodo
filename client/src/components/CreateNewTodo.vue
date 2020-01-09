<template>
    <div id="app-create-new-item">
        <div class="nes-container with-title" v-if='isLoggedIn'>
            <p class="title">{{ component_title }}</p>
            <div class="nes-field">
                <label for="title">Title</label>
                <input type="text" id="title" class="nes-input" placeholder="Todo Item Title" v-model="title">
            </div>
            <div class="nes-field">
                <label for="content">Content</label>
                <textarea id="content" class="nes-textarea" placeholder="Todo Item Content..." v-model="content"></textarea>
            </div>
            <button type="button" class="nes-btn is-success" v-on:click="createNewItem">Submit</button>
        </div>
    </div>
</template>

<script>
 export default {
     name: 'CreateNewTodo',
     props: {
         component_title: String
     },
     data: function() {
         return {
             isLoggedIn: localStorage.token != undefined && localStorage.token != '',
             title: '',
             content: ''             
         }
     },
     methods: {
         createNewItem: function() {
             this.$axios({
                 method: 'post',
                 url: 'http://localhost:8000/todos',
                 data: {
                     "title": this.title,
                     "content": this.content,
                     "due_date": "2019-12-28T14:39:48.193Z"
                 },
                 headers: {'Authorization': 'Bearer ' + localStorage.token}
             }).then(response => {
                 // console.log(response)
                 this.$root.$emit('new_todo_added', response.data)
             }).catch(error => {
                 // console.log(error)
                 if (error.response.status === 401) {
                     localStorage.removeItem('token')
                 }
                 this.errored = true
             }) .finally(() => this.loading = false)
         }
     },
     mounted () {
         this.$root.$on('logged_in', () => {
             this.isLoggedIn = localStorage.token != undefined && localStorage.token != '';
         });
     }
 }
</script>
