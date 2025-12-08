
import { createRouter, createWebHistory } from 'vue-router';

import LoginPage from '../components/LoginPage.vue';
import OtpPage from '../components/OtpPage.vue';
import PrivacyPolicy from '../components/PrivacyPolicy.vue';
import CreateProfilePage from '../components/CreateProfilePage.vue';
import DashboardPage from '../components/DashboardPage.vue';
import AddChildPage from '../components/AddChildPage.vue';
import EditProfilePage from '../components/EditProfilePage.vue';
import EditChildPage from '../components/EditChildPage.vue';
import TestPage from '../components/TestPage.vue';
import GameSessionPage from '../components/GameSessionPage.vue';
import GrowthChartPage from '../components/GrowthChartPage.vue';

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
    path: '/test/:childId/:skillCategory',
    name: 'TestPage',
    component: TestPage,
    props: true,
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
  },
  {
    path: '/test/:childId/:skillCategory', 
    name: 'TestPage',
    component: TestPage,
    props: true, 
  },
  {
    path: '/test/:childId/:skillCategory',
    name: 'TestPage',
    component: TestPage,
    props: true,
  },
  {
    path: '/play/:childId/:skillCategory',
    name: 'GameSessionPage',
    component: GameSessionPage,
    props: true,
  },
  {
    path: '/growth-chart/:childId', 
    name: 'GrowthChartPage',
    component: GrowthChartPage,
    props: true,
  }

];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes, 
});
router.beforeEach((to, from, next) => {
  const loggedInUser = localStorage.getItem('loggedInUserPhone');
  const isLoginPage = to.name === 'Login' || to.name === 'OtpPage' || to.name === 'PrivacyPolicy';

  if (loggedInUser && isLoginPage) {
    next({ name: 'Dashboard' });
  } else if (!loggedInUser && to.name !== 'Login' && to.name !== 'PrivacyPolicy' && to.name !== 'OtpPage' && to.name !== 'CreateProfile') {
    next({ name: 'Login' });
  } else {
    next();
  }
});


export default router;