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
