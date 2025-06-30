const { createApp, ref } = Vue;

createApp({
  setup() {
    const message = ref('');

    const fetchMessage = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/hello');
        const data = await res.json();
        message.value = data.message;
      } catch (err) {
        message.value = 'Error fetching data';
      }
    };

    return { message, fetchMessage };
  }
}).mount('#app');
