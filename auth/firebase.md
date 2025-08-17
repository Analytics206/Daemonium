npm install firebase

// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCZnlUW9-DbAaz3zfiwm9PWph1B8rWu7nc",
  authDomain: "daimonium-f9277.firebaseapp.com",
  projectId: "daimonium-f9277",
  storageBucket: "daimonium-f9277.firebasestorage.app",
  messagingSenderId: "189296781243",
  appId: "1:189296781243:web:ae044dc8b8d515e2e1069e",
  measurementId: "G-KY487X2TG8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);