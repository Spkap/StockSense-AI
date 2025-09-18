// Firebase configuration - uses environment variables
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';


const firebaseConfig = {
  apiKey: "AIzaSyCRkGrmzr3Xw_8-ezY5O8n-ocXbUc1xuWo",
  authDomain: "stocksense-e7226.firebaseapp.com",
  projectId: "stocksense-e7226",
  storageBucket: "stocksense-e7226.firebasestorage.app",
  messagingSenderId: "655472957148",
  appId: "1:655472957148:web:5528ffd1b4d744d565c619"
};

const app = initializeApp(firebaseConfig);


export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();



export default app;
