import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../components/LoginPage.vue';
import PrivacyPolicy from '../components/PrivacyPolicy.vue';
import OtpPage from '../components/OtpPage.vue';
import CreateProfilePage from '../components/CreateProfilePage.vue'; // کامپوننت جدید را وارد کنید

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/privacy',
    name: 'PrivacyPolicy',
    component: PrivacyPolicy,
  },
  {
    path: '/otp/:phoneNumber', 
    name: 'OtpPage',
    component: OtpPage,
    props: true, 
  },
  {
    path: '/otp/:phoneNumber',
    name: 'OtpPage',
    component: OtpPage,
    props: true,
  },
  {
    path: '/create-profile',
    name: 'CreateProfile',
    component: CreateProfilePage,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;