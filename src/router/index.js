import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../components/LoginPage.vue';
import OtpPage from '../components/OtpPage.vue';
import PrivacyPolicy from '../components/PrivacyPolicy.vue';
import CreateProfilePage from '../components/CreateProfilePage.vue';
import DashboardPage from '../components/DashboardPage.vue';
import AddChildPage from '../components/AddChildPage.vue';
import EditProfilePage from '../components/EditProfilePage.vue';
import EditChildPage from '../components/EditChildPage.vue';
const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/otp/:phoneNumber',
    name: 'OtpPage',
    component: OtpPage,
    props: true, 
  },
  {
    path: '/privacy',
    name: 'PrivacyPolicy',
    component: PrivacyPolicy,
  },
  {
    path: '/create-profile/:phoneNumber',
    name: 'CreateProfile',
    component: CreateProfilePage,
    props: true,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardPage,
  },
  {
    path: '/add-child',
    name: 'AddChild',
    component: AddChildPage,
  },
  {
    path: '/edit-profile',
    name: 'EditProfile',
    component: EditProfilePage,
  },
  {
    path: '/edit-child/:childId',
    name: 'EditChild',
    component: EditChildPage,
    props: true,
  }
];
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes, 
});
export default router;