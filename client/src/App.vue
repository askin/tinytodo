<template>
    <div id="app">
        <Login component_title="Login"/>
        <CreateNewTodo component_title="Create New ToDo"/>
        <ListTodoItems component_title="ToDos"/>
    </div>
</template>

<script>
 import Login from './components/Login.vue'
 import CreateNewTodo from './components/CreateNewTodo.vue'
 import ListTodoItems from './components/ListTodoItems.vue'
 
 export default {
     name: 'app',
     components: {
         Login,
         CreateNewTodo,
         ListTodoItems,
     }
 }
</script>

<style>
 #app {
     -webkit-font-smoothing: antialiased;
     -moz-osx-font-smoothing: grayscale;
     color: #2c3e50;
     margin-top: 60px;
 }
</style>
