<template>
  <div class="dashboard-layout">
    
    <aside class="left-panel">
      <div class="panel-header">
        <h3>تحلیل نوروچی</h3>
      </div>
      <div class="analysis-content">
        <div v-if="isLoading" class="loading-spinner">در حال تحلیل...</div>
        <div v-else class="analysis-text" v-html="formattedAnalysis"></div>
        <div v-if="!analysis && !isLoading" class="empty-state">
          رکوردی ثبت کنید تا تحلیل نمایش داده شود.
        </div>
      </div>
    </aside>
    <main class="center-panel">
      
      <div class="input-card">
        <div class="card-header">
          <h3>ثبت وضعیت کنونی ({{ currentChildGender === 'female' ? 'دختر' : 'پسر' }})</h3>
        </div>
        <form @submit.prevent="submitNewRecord" class="input-row">
          <div class="input-group">
            <label>قد (cm)</label>
            <input type="number" step="0.1" v-model.number="newRecord.height" placeholder="مثلا: 85.5">
          </div>
          <div class="input-group">
            <label>وزن (kg)</label>
            <input type="number" step="0.1" v-model.number="newRecord.weight" placeholder="مثلا: 12.2">
          </div>
          <div class="input-group">
            <label>دور سر (cm)</label>
            <input type="number" step="0.1" v-model.number="newRecord.head_circumference" placeholder="مثلا: 48">
          </div>
          <button type="submit" class="btn-submit" :disabled="isSubmitting">
            {{ isSubmitting ? '...' : 'ثبت رکورد' }}
          </button>
        </form>
      </div>

      <div class="chart-section">
        <div class="tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="chart-container">
          <Line v-if="chartData.datasets.length" :data="chartData" :options="chartOptions" />
          <div v-else class="no-data">داده‌ای موجود نیست.</div>
        </div>
      </div>

      <div class="chat-bar">
        <button class="mic-btn">🎤</button>
        <input type="text" placeholder="سوالی دارید؟" />
        <button class="send-btn">➤</button>
      </div>
    </main>

    <aside class="right-panel">
      <router-link to="/dashboard" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        <span>بازگشت به داشبورد</span>
      </router-link>

      <div class="child-selector">
        <div 
          v-for="child in children" 
          :key="child.id" 
          class="child-avatar"
          :class="{ active: child.id == childId }"
          @click="switchChild(child.id)"
        >
          <img src="@/assets/logo.svg" alt="Child" /> 
          <div class="child-info-select">
            <span class="name">{{ child.name }}</span>
            <span class="gender-badge">{{ child.gender === 'female' ? 'دختر' : 'پسر' }}</span>
          </div>
        </div>
      </div>

      <div class="timeline-header">تاریخچه رشد</div>
      
      <div class="timeline-container">
        <div v-for="record in reversedRecords" :key="record.id" class="timeline-item">
          <div class="timeline-icon">
            <span v-if="activeTab === 'height'">📏</span>
            <span v-else-if="activeTab === 'weight'">⚖️</span>
            <span v-else>🧠</span>
          </div>
          <div class="timeline-content">
            <span class="timeline-label">{{ getTabLabel(activeTab) }}</span>
            <span class="timeline-value">
                {{ activeTab === 'height' ? record.height : (activeTab === 'weight' ? record.weight : record.head_circumference) }}
                <small>{{ activeTab === 'weight' ? 'kg' : 'cm' }}</small>
            </span>
          </div>
          <div class="timeline-date">{{ formatDate(record.date) }}</div>
        </div>
      </div>

      <div class="user-footer">
        <div class="user-info">
          <span>{{ user.parent_name }}</span>
          <div class="avatar-circle">👤</div>
        </div>
      </div>
    </aside>

  </div>
</template>

<script>
import axios from 'axios';
import { Line } from 'vue-chartjs';
import { 
  Chart as ChartJS, Title, Tooltip, Legend, LineElement, CategoryScale, 
  LinearScale, PointElement, Filler 
} from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement, Filler);

const WHO_BOYS = {
  height: [ 
    {m:0, n3:44.2, n2:46.1, n1:48.0, med:49.9, p1:51.8, p2:53.7, p3:55.6},
    {m:6, n3:61.2, n2:63.3, n1:65.5, med:67.6, p1:69.8, p2:71.9, p3:74.0},
    {m:12, n3:68.6, n2:71.0, n1:73.4, med:75.7, p1:78.1, p2:80.5, p3:82.9},
    {m:24, n3:78.7, n2:81.7, n1:84.8, med:87.8, p1:90.9, p2:93.9, p3:97.0},
    {m:36, n3:85.0, n2:88.7, n1:92.4, med:96.1, p1:99.8, p2:103.5, p3:107.2},
    {m:48, n3:90.7, n2:94.9, n1:99.1, med:103.3, p1:107.5, p2:111.7, p3:115.9},
    {m:60, n3:96.1, n2:100.7, n1:105.3, med:110.0, p1:114.6, p2:119.2, p3:123.9}
  ],
  weight: [ 
    {m:0, n3:2.1, n2:2.5, n1:2.9, med:3.3, p1:3.9, p2:4.4, p3:5.0},
    {m:6, n3:5.7, n2:6.4, n1:7.1, med:7.9, p1:8.8, p2:9.8, p3:10.9},
    {m:12, n3:6.9, n2:7.7, n1:8.6, med:9.6, p1:10.8, p2:12.0, p3:13.3},
    {m:24, n3:8.6, n2:9.7, n1:10.8, med:12.2, p1:13.6, p2:15.3, p3:17.1},
    {m:36, n3:10.0, n2:11.3, n1:12.7, med:14.3, p1:16.2, p2:18.3, p3:20.7},
    {m:48, n3:11.2, n2:12.7, n1:14.4, med:16.3, p1:18.6, p2:21.2, p3:24.2},
    {m:60, n3:12.4, n2:14.1, n1:16.0, med:18.3, p1:21.0, p2:24.2, p3:27.9}
  ],
  head: [ 
    {m:0, n3:30.7, n2:31.9, n1:33.2, med:34.5, p1:35.7, p2:37.0, p3:38.3},
    {m:6, n3:39.7, n2:40.9, n1:42.1, med:43.3, p1:44.6, p2:45.8, p3:47.0},
    {m:12, n3:42.2, n2:43.5, n1:44.8, med:46.1, p1:47.4, p2:48.6, p3:49.9},
    {m:24, n3:44.2, n2:45.5, n1:46.9, med:48.3, p1:49.6, p2:51.0, p3:52.3},
    {m:36, n3:45.2, n2:46.6, n1:48.0, med:49.5, p1:50.9, p2:52.3, p3:53.7},
    {m:48, n3:45.8, n2:47.3, n1:48.7, med:50.2, p1:51.7, p2:53.1, p3:54.6},
    {m:60, n3:46.3, n2:47.7, n1:49.2, med:50.7, p1:52.2, p2:53.7, p3:55.2}
  ]
};

const WHO_GIRLS = {
  height: [
    {m:0, n3:43.6, n2:45.4, n1:47.3, med:49.1, p1:51.0, p2:52.9, p3:54.7},
    {m:6, n3:58.9, n2:61.2, n1:63.5, med:65.7, p1:68.0, p2:70.3, p3:72.5},
    {m:12, n3:66.3, n2:68.9, n1:71.4, med:74.0, p1:76.6, p2:79.2, p3:81.7},
    {m:24, n3:76.0, n2:79.3, n1:82.5, med:85.7, p1:88.9, p2:92.2, p3:95.4},
    {m:36, n3:83.6, n2:87.4, n1:91.2, med:95.1, p1:98.9, p2:102.7, p3:106.5},
    {m:48, n3:89.8, n2:94.1, n1:98.4, med:102.7, p1:107.0, p2:111.3, p3:115.7},
    {m:60, n3:95.2, n2:99.9, n1:104.7, med:109.4, p1:114.2, p2:118.9, p3:123.7}
  ],
  weight: [
    {m:0, n3:2.0, n2:2.4, n1:2.8, med:3.2, p1:3.7, p2:4.2, p3:4.8},
    {m:6, n3:5.1, n2:5.7, n1:6.5, med:7.3, p1:8.2, p2:9.3, p3:10.6},
    {m:12, n3:6.3, n2:7.0, n1:7.9, med:8.9, p1:10.1, p2:11.5, p3:13.1},
    {m:24, n3:8.1, n2:9.0, n1:10.2, med:11.5, p1:13.0, p2:14.8, p3:17.0},
    {m:36, n3:9.6, n2:10.8, n1:12.2, med:13.9, p1:15.8, p2:18.1, p3:20.9},
    {m:48, n3:10.9, n2:12.3, n1:14.0, med:16.1, p1:18.5, p2:21.5, p3:25.2},
    {m:60, n3:12.1, n2:13.7, n1:15.8, med:18.2, p1:21.2, p2:24.9, p3:29.5}
  ],
  head: [
    {m:0, n3:30.3, n2:31.5, n1:32.7, med:33.9, p1:35.1, p2:36.2, p3:37.4},
    {m:6, n3:38.3, n2:39.6, n1:40.9, med:42.2, p1:43.5, p2:44.8, p3:46.1},
    {m:12, n3:40.8, n2:42.2, n1:43.5, med:44.9, p1:46.3, p2:47.6, p3:49.0},
    {m:24, n3:43.0, n2:44.4, n1:45.8, med:47.2, p1:48.6, p2:50.0, p3:51.4},
    {m:36, n3:44.3, n2:45.7, n1:47.1, med:48.5, p1:49.9, p2:51.3, p3:52.7},
    {m:48, n3:45.1, n2:46.5, n1:47.9, med:49.3, p1:50.8, p2:52.2, p3:53.6},
    {m:60, n3:45.7, n2:47.1, n1:48.5, med:49.9, p1:51.3, p2:52.8, p3:54.2}
  ]
};

export default {
  name: 'GrowthChartPage',
  components: { Line },
  props: {
    childId: { type: [String, Number], required: true }
  },
  data() {
    return {
      isLoading: false,
      isSubmitting: false,
      user: {},
      children: [],
      records: [],
      analysis: '',
      activeTab: 'weight',
      tabs: [
        { id: 'weight', label: 'وزن' },
        { id: 'head', label: 'دور سر' },
        { id: 'height', label: 'قد' },
      ],
      newRecord: { height: null, weight: null, head_circumference: null },
      currentChildBirthDate: null,
      currentChildGender: 'male',
    };
  },
  computed: {
    reversedRecords() {
      return [...this.records].reverse();
    },
    formattedAnalysis() {
        if (!this.analysis) return '';
        let text = this.analysis.replace(/\n/g, '<br/>');
        return text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    },
  
    currentWHOData() {
        const dataset = this.currentChildGender === 'female' ? WHO_GIRLS : WHO_BOYS;
        return dataset[this.activeTab];
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'nearest', axis: 'x', intersect: false },
        plugins: {
            legend: { display: false },
            tooltip: {
                rtl: true,
                bodyFont: { family: 'Vazir' },
                titleFont: { family: 'Vazir' },
                callbacks: {
                    title: (items) => {
                        const m = items[0].parsed.x;
                        const y = Math.floor(m / 12);
                        const rm = Math.floor(m % 12);
                        return `سن: ${m.toFixed(1)} ماه (${y > 0 ? y + ' سال ' : ''}${rm > 0 ? rm + ' ماه' : ''})`;
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'linear',
                title: { display: true, text: 'سن (ماه)', font: { family: 'Vazir' } },
                ticks: { stepSize: 6, font: { family: 'Vazir' } },
                min: 0,
                max: 60 
            },
            y: {
                title: { display: true, text: this.getUnit(), font: { family: 'Vazir' } },
                ticks: { font: { family: 'Vazir' } }
            }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4, borderWidth: 1 }
        }
      };
    },
    chartData() {
        const whoData = this.currentWHOData;
        
        const userPoints = this.records.map(r => {
            if (!this.currentChildBirthDate) return null;
            const birth = new Date(this.currentChildBirthDate);
            const recordDate = new Date(r.date);
            const diffTime = Math.abs(recordDate - birth);
            const diffMonths = diffTime / (1000 * 60 * 60 * 24 * 30.44); 
            
            let val = null;
            if (this.activeTab === 'height') val = r.height;
            else if (this.activeTab === 'weight') val = r.weight;
            else val = r.head_circumference;

            return { x: diffMonths, y: val };
        }).filter(p => p && p.y);

        return {
            datasets: [
                {
                    label: 'کودک شما',
                    data: userPoints,
                    borderColor: '#2e7d32', 
                    backgroundColor: '#2e7d32',
                    borderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    fill: false,
                    zIndex: 20
                },
                {
                    label: 'Median',
                    data: whoData.map(d => ({x: d.m, y: d.med})),
                    borderColor: '#f57c00', 
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: '+3 SD',
                    data: whoData.map(d => ({x: d.m, y: d.p3})),
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    fill: '+1'
                },
                {
                    label: '+2 SD',
                    data: whoData.map(d => ({x: d.m, y: d.p2})),
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(156, 39, 176, 0.2)',
                    fill: '+1'
                },
                {
                    label: '+1 SD',
                    data: whoData.map(d => ({x: d.m, y: d.p1})),
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(156, 39, 176, 0.3)',
                    fill: '+1' 
                },
                 {
                    label: '-1 SD',
                    data: whoData.map(d => ({x: d.m, y: d.n1})),
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(156, 39, 176, 0.3)',
                    fill: '-1' 
                },
                 {
                    label: '-2 SD',
                    data: whoData.map(d => ({x: d.m, y: d.n2})),
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(156, 39, 176, 0.2)',
                    fill: '-1' 
                },
                 {
                    label: '-3 SD',
                    data: whoData.map(d => ({x: d.m, y: d.n3})),
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    fill: '-1' 
                }
            ]
        };
    }
  },
  methods: {
    getUnit() {
        return this.activeTab === 'weight' ? 'کیلوگرم (kg)' : 'سانتی‌متر (cm)';
    },
    getTabLabel(key) {
        const map = { height: 'قد', weight: 'وزن', head: 'دور سر' };
        return map[key];
    },
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('fa-IR');
    },
    async fetchData() {
        this.isLoading = true;
        const phone = localStorage.getItem('loggedInUserPhone');
        try {
            const userRes = await axios.get(`/me/${phone}`);
            this.user = userRes.data;
            this.children = userRes.data.children;

            const currentChild = this.children.find(c => c.id == this.childId);
            if(currentChild) {
                this.currentChildBirthDate = currentChild.birth_date;
                this.currentChildGender = (currentChild.gender === 'دختر' || currentChild.gender === 'female') ? 'female' : 'male';
            }

            const chartRes = await axios.get(`/children/${this.childId}/growth-chart`);
            this.records = chartRes.data.records;
            this.analysis = chartRes.data.analysis;
        } catch (e) {
            console.error(e);
        } finally {
            this.isLoading = false;
        }
    },
    async submitNewRecord() {
        if(!this.newRecord.height && !this.newRecord.weight) return;
        this.isSubmitting = true;
        try {
            await axios.post(`/children/${this.childId}/growth-records`, this.newRecord);
            this.newRecord = { height: null, weight: null, head_circumference: null };
            await this.fetchData();
        } catch (e) {
            alert('خطا در ثبت');
        } finally {
            this.isSubmitting = false;
        }
    },
    switchChild(id) {
        this.$router.push(`/growth-chart/${id}`);
        setTimeout(() => window.location.reload(), 10);
    }
  },
  mounted() {
    this.fetchData();
  }
}
</script>

<style scoped>
.dashboard-layout {
  display: grid;
  grid-template-columns: 300px 1fr 280px; 
  height: 100vh;
  background-color: #f3e5f5;
  font-family: 'Vazir', sans-serif;
  direction: rtl;
  overflow: hidden;
}

.right-panel {
  order: 1; 
  background: rgba(255, 255, 255, 0.8);
  padding: 20px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #fff; 
}

.center-panel {
  order: 2;
  padding: 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.left-panel {
  order: 3;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  padding: 20px;
  border-right: 1px solid #fff;
  display: flex;
  flex-direction: column;
}

.panel-header h3 { color: #4a148c; margin-bottom: 20px; font-size: 1.2rem; }
.analysis-content {
  flex: 1; overflow-y: auto; font-size: 0.95rem; line-height: 1.8;
  color: #333; background: #fff; padding: 15px; border-radius: 15px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.empty-state { color: #888; text-align: center; margin-top: 50px; }

.input-card {
  background: #fff; padding: 20px; border-radius: 20px;
  box-shadow: 0 5px 20px rgba(106, 27, 154, 0.05);
}
.card-header h3 { margin: 0 0 15px 0; font-size: 1.1rem; color: #333; }
.input-row { display: flex; gap: 15px; align-items: flex-end; flex-wrap: wrap; }
.input-group { flex: 1 1 150px; display: flex; flex-direction: column; }
.input-group label { font-size: 0.85rem; color: #666; margin-bottom: 5px; }
.input-group input {
  padding: 10px; border: 1px solid #e0e0e0; border-radius: 10px;
  text-align: center; font-size: 1rem; width: 100%; box-sizing: border-box;
}
.btn-submit {
  background: #8e44ad; color: #fff; border: none; padding: 0 25px;
  height: 42px; border-radius: 10px; cursor: pointer; font-weight: bold;
  flex: 1 1 auto; transition: 0.2s;
}
.btn-submit:hover { background: #7b1fa2; }
.btn-submit:disabled { background: #ccc; }

.chart-section {
  background: #fff; border-radius: 20px; padding: 20px; flex: 1;
  display: flex; flex-direction: column; box-shadow: 0 5px 20px rgba(106, 27, 154, 0.05);
}
.tabs {
  display: flex; justify-content: center; margin-bottom: 20px;
  background: #f3f0f7; border-radius: 12px; padding: 5px;
  width: fit-content; margin-right: auto; margin-left: auto;
}
.tab-btn {
  padding: 8px 30px; border: none; background: transparent; cursor: pointer;
  border-radius: 8px; color: #666; font-weight: bold;
}
.tab-btn.active { background: #fff; color: #8e44ad; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.chart-container { flex: 1; position: relative; min-height: 300px; display: flex; justify-content: center; align-items: center; }
.no-data { color: #999; }

.chat-bar {
  background: #fff; border-radius: 50px; padding: 8px 15px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}
.chat-bar input { flex: 1; border: none; outline: none; font-family: inherit; }
.mic-btn, .send-btn { background: none; border: none; cursor: pointer; color: #666; }

.child-selector { display: flex; flex-direction: column; gap: 10px; margin-bottom: 30px; }
.child-avatar {
  display: flex; align-items: center; gap: 10px; padding: 10px;
  border-radius: 12px; cursor: pointer; transition: 0.2s; opacity: 0.6;
}
.child-avatar.active { background: #fff; opacity: 1; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.child-avatar img { width: 35px; height: 35px; border-radius: 50%; }
.child-info-select { display: flex; flex-direction: column; }
.gender-badge { font-size: 0.7rem; color: #888; }

.timeline-header { font-weight: bold; margin-bottom: 15px; color: #444; }
.timeline-container { flex: 1; overflow-y: auto; border-right: 2px solid #e0e0e0; padding-right: 15px; }
.timeline-item { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; position: relative; }
.timeline-item::before {
  content: ''; position: absolute; right: -21px; top: 50%;
  width: 10px; height: 10px; background: #8e44ad; border-radius: 50%;
  transform: translateY(-50%); border: 2px solid #fff;
}
.timeline-icon {
  width: 40px; height: 40px; background: #f3e5f5; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; color: #8e44ad;
}
.timeline-content { flex: 1; display: flex; flex-direction: column; }
.timeline-label { font-size: 0.8rem; color: #777; }
.timeline-value { font-weight: bold; font-size: 1.1rem; color: #333; }
.timeline-value small { font-size: 0.7rem; color: #999; }
.timeline-date { font-size: 0.75rem; color: #aaa; }

.back-btn {
  display: flex; align-items: center; gap: 10px; text-decoration: none;
  color: #6a1b9a; font-weight: bold; font-size: 1rem; margin-bottom: 25px;
  padding: 10px 15px; border-radius: 12px; transition: all 0.2s ease;
}
.back-btn:hover {
  background-color: #fff; border-color: #e1bee7; color: #4a148c;
  box-shadow: 0 2px 8px rgba(106, 27, 154, 0.1); transform: translateX(5px);
}
.back-btn svg { transform: rotate(180deg); }
.user-footer { margin-top: auto; border-top: 1px solid #eee; padding-top: 15px; }
.user-info { display: flex; align-items: center; justify-content: space-between; background: #fff; padding: 10px; border-radius: 12px; }

@media (max-width: 1024px) {
  .dashboard-layout { grid-template-columns: 1fr; height: auto; overflow-y: auto; }
  .left-panel, .right-panel, .center-panel { border: none; padding: 15px; order: unset; }
  .right-panel { order: -1; }
  .input-row { flex-direction: column; align-items: stretch; }
  .input-group { width: 100%; }
  .btn-submit { width: 100%; margin-top: 10px; }
}
</style>