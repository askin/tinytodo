<template>    
    <div id="list-todo-items">
        <div  v-if="isLoggedIn">
            <div class="nes-container with-title" id="app-4">
                
                <p class="title">{{ component_title }}</p>
                <div v-bind:key="idx" v-for="(todo, idx) in todos" >
                    <div class="nes-container is-dark with-title" >
                        <p class="title">{{ todo.title }}</p>
                        <p>{{ todo.content }}</p>
                        <button type="button" class="nes-btn is-error"
                                v-on:click="show( todo.uuid )">
                            Delete
                        </button>

                        <button type="button" v-if="!todo.is_done" class="nes-btn is-success" v-on:click="set_done(todo.uuid, true)">Done</button>
                        <button type="button" v-if="todo.is_done" class="nes-btn is-success" v-on:click="set_done(todo.uuid, false)">Not Done</button>

                        <section>
                            <dialog class="nes-dialog" :name="todo.uuid" :id="todo.uuid" >
                                <form method="dialog">
                                    <p class="title">Delete Todo Item!</p>
                                    <p>Alert: "{{ todo.title  }}" will be deleted!</p>
                                    <menu class="dialog-menu">
                                        <button class="nes-btn">Cancel</button>
                                        <button class="nes-btn is-error" v-on:click="delete_item( todo.uuid )">Confirm</button>
                                    </menu>
                                </form>
                            </dialog>
                        </section>

                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
 export default {
     name: 'ListTodoItems',
     props: {
         component_title: String
     },
     data: function() {
         return {
             'todos': [
             ],
             'isLoggedIn': localStorage.token != undefined && localStorage.token != '',
         }
     },
     methods: {
         show ( uuid ) {
             // FIXME: Works only chrome
             document.getElementById( uuid ).showModal()
         },
         get_todo_items: function() {
             this.$axios({
                 method: 'get',
                 url: 'http://localhost:8000/todos',
                 timeout: 1000,
                 headers: {'Authorization': 'Bearer ' + localStorage.token},
             }).then(response => {
                 // console.log(response)
                 this.todos = response.data
                 // app4.todos.push(response.data)
             }).catch(error => {
                 // console.log(error)
                 if (error.response.status === 401) {
                     localStorage.removeItem('token')
                 }
                 this.errored = true
             }) .finally(() => this.loading = false)             
         },
         delete_item: function(_uuid) {

             this.$axios.delete(
                 'http://localhost:8000/todos/' + _uuid,
                 {headers: {'Authorization': 'Bearer ' + localStorage.token},}
             ).then(response => {
                 // console.log(response)
                 if (response.status === 200) {
                     for (var i = 0; i < this.todos.length; i++) {
                         if (this.todos[i].uuid == _uuid) {
                             this.todos.splice(i, 1)
                             break;
                         }
                     }                     
                 }

                 // this.todos = response.data
                 // app4.todos.push(response.data)
             }).catch(error => {
                 // console.log(error)
                 if (error.response.status === 401) {
                     localStorage.removeItem('token')
                 }
                 this.errored = true
             }) .finally(() => this.loading = false)             
         },
         set_done: function(_uuid, is_done) {

             this.$axios.patch(
                 'http://localhost:8000/todos/' + _uuid,
                 {'is_done': is_done},
                 {headers: {'Authorization': 'Bearer ' + localStorage.token},}
             ).then(response => {
                 // console.log(response)
                 if (response.status === 200) {
                     for (var i = 0; i < this.todos.length; i++) {
                         if (this.todos[i].uuid == _uuid) {
                             this.todos[i].is_done = is_done;
                             break;
                         }
                     }                     
                 }
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

         if (this.isLoggedIn) this.get_todo_items();

         this.$root.$on('new_todo_added', (data) => {
             this.todos.push(data);
         });

         this.$root.$on('logged_in', () => {
             this.isLoggedIn = localStorage.token != undefined && localStorage.token != '';
             if (this.isLoggedIn) this.get_todo_items();
         });

     }
 }
</script>
