
import { createRouter, createWebHistory } from 'vue-router';

const LoginPage = () => import('../components/LoginPage.vue');
import LandingPage from '../components/LandingPage.vue';
const TestHistoryPage = () => import('../components/TestHistoryPage.vue');
const OtpPage = () => import('../components/OtpPage.vue');
const PrivacyPolicy = () => import('../components/PrivacyPolicy.vue');
const CreateProfilePage = () => import('../components/CreateProfilePage.vue');
const DashboardPage = () => import('../components/DashboardPage.vue');
const AddChildPage = () => import('../components/AddChildPage.vue');
const EditProfilePage = () => import('../components/EditProfilePage.vue');
const EditChildPage = () => import('../components/EditChildPage.vue');
const TestPage = () => import('../components/TestPage.vue');
const GameSessionPage = () => import('../components/GameSessionPage.vue');
const GrowthChartPage = () => import('../components/GrowthChartPage.vue');

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: LandingPage,
  },
  {
    path: '/login',
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
    path: '/test-history/:childId',
    name: 'TestHistory',
    component: TestHistoryPage,
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
  const isLoginPage = to.name === 'Login' || to.name === 'OtpPage';
  const publicPages = ['Landing', 'Login', 'OtpPage', 'PrivacyPolicy', 'CreateProfile'];

  if (loggedInUser && isLoginPage) {
    next(localStorage.getItem('needsChildOnboarding') ? { name: 'AddChild', query: { onboarding: '1' } } : { name: 'Dashboard' });
  } else if (loggedInUser && localStorage.getItem('needsChildOnboarding') && !['Landing', 'PrivacyPolicy', 'AddChild'].includes(to.name)) {
    next({ name: 'AddChild', query: { onboarding: '1' } });
  } else if (!loggedInUser && !publicPages.includes(to.name)) {
    next({ name: 'Login' });
  } else {
    next();
  }
});


export default router;
