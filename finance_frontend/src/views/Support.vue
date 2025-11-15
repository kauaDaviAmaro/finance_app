<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { sendSupportMessage } from '../services/api/support.api'
import { ApiError } from '../services/api'
import { HelpCircle, Mail, MessageSquare, Send, CheckCircle2, AlertCircle } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const authStore = useAuthStore()

const activeTab = ref<'contact' | 'faq'>('contact')
const submitting = ref(false)
const successMessage = ref<string | null>(null)
const errorMessage = ref<string | null>(null)

const contactForm = ref({
  email: authStore.user?.email || '',
  subject: '',
  message: '',
  category: 'general' as 'general' | 'technical' | 'billing' | 'feature'
})

const faqItems = [
  {
    question: 'Como criar alertas de preço?',
    answer: 'Acesse a página de Alertas no menu principal, clique em "Criar Alerta" e configure o ticker, tipo de alerta (preço acima/abaixo) e o valor desejado. Você receberá notificações por email quando o alerta for acionado.'
  },
  {
    question: 'Como funciona o Scanner PRO?',
    answer: 'O Scanner PRO permite buscar ações com base em critérios técnicos avançados como RSI, MACD, volume e outros indicadores. Esta funcionalidade está disponível apenas para assinantes PRO.'
  },
  {
    question: 'Como atualizar meu plano para PRO?',
    answer: 'Acesse a página de Assinatura no menu ou clique no botão "PRO" na barra de navegação. Você será redirecionado para completar o pagamento via Stripe.'
  },
  {
    question: 'Como gerenciar minha assinatura?',
    answer: 'Acesse a página de Assinatura e clique em "Gerenciar Assinatura" para acessar o portal do Stripe, onde você pode atualizar seu método de pagamento, cancelar ou alterar seu plano.'
  },
  {
    question: 'Os dados são atualizados em tempo real?',
    answer: 'Os preços das ações são atualizados periodicamente durante o horário de funcionamento do mercado. Alertas são verificados a cada minuto e notificações são enviadas imediatamente quando acionadas.'
  },
  {
    question: 'Como adicionar ações ao meu portfólio?',
    answer: 'Na página de Portfólio, clique em "Adicionar Ativo", informe o ticker, quantidade e preço de compra. Você pode acompanhar o desempenho de seus investimentos em tempo real.'
  },
  {
    question: 'Preciso de ajuda técnica. Como entrar em contato?',
    answer: 'Use o formulário de contato nesta página selecionando a categoria "Técnico" ou envie um email diretamente para suporte@financeapp.com. Nossa equipe responderá em até 24 horas.'
  },
  {
    question: 'Como cancelar minha conta?',
    answer: 'Para cancelar sua conta, entre em contato através do formulário de suporte ou envie um email para suporte@financeapp.com. Lembre-se de cancelar sua assinatura PRO antes, se aplicável.'
  }
]

const expandedFaq = ref<number | null>(null)

function toggleFaq(index: number) {
  expandedFaq.value = expandedFaq.value === index ? null : index
}

async function submitContactForm() {
  if (!contactForm.value.subject.trim() || !contactForm.value.message.trim()) {
    errorMessage.value = 'Por favor, preencha todos os campos obrigatórios.'
    return
  }

  submitting.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    // Se o usuário estiver autenticado, usar o email dele, senão usar o email do formulário
    const email = authStore.user?.email || contactForm.value.email || ''
    if (!email) {
      errorMessage.value = 'Por favor, informe seu email.'
      return
    }
    await sendSupportMessage({
      email: email,
      category: contactForm.value.category,
      subject: contactForm.value.subject,
      message: contactForm.value.message
    })
    
    successMessage.value = 'Mensagem enviada com sucesso! Nossa equipe entrará em contato em breve.'
    contactForm.value.subject = ''
    contactForm.value.message = ''
    contactForm.value.category = 'general'
    if (!authStore.user) {
      contactForm.value.email = ''
    }
  } catch (err) {
    if (err instanceof ApiError) {
      errorMessage.value = err.message || 'Erro ao enviar mensagem. Por favor, tente novamente.'
    } else {
      errorMessage.value = 'Erro ao enviar mensagem. Por favor, tente novamente ou envie um email diretamente para suporte@financeapp.com'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <Navbar />
    <div class="support-container">
      <h1 class="page-title">Suporte</h1>
      <p class="page-subtitle">Estamos aqui para ajudar. Entre em contato ou consulte nossas perguntas frequentes.</p>

      <div class="tabs">
        <button 
          :class="['tab', { active: activeTab === 'contact' }]"
          @click="activeTab = 'contact'"
        >
          <Mail :size="18" />
          <span>Contato</span>
        </button>
        <button 
          :class="['tab', { active: activeTab === 'faq' }]"
          @click="activeTab = 'faq'"
        >
          <HelpCircle :size="18" />
          <span>Perguntas Frequentes</span>
        </button>
      </div>

      <!-- Contact Form -->
      <div v-if="activeTab === 'contact'" class="content-section">
        <div class="support-card">
          <div class="card-header">
            <MessageSquare :size="24" />
            <h2>Envie sua Mensagem</h2>
          </div>

          <div v-if="successMessage" class="alert success">
            <CheckCircle2 :size="18" />
            <span>{{ successMessage }}</span>
          </div>
          <div v-if="errorMessage" class="alert error">
            <AlertCircle :size="18" />
            <span>{{ errorMessage }}</span>
          </div>

          <form @submit.prevent="submitContactForm" class="contact-form">
            <div class="form-field" v-if="!authStore.user">
              <label class="label">Email *</label>
              <input
                v-model="contactForm.email"
                type="email"
                class="input"
                placeholder="seu@email.com"
                required
                :disabled="submitting"
              />
            </div>

            <div class="form-field">
              <label class="label">Categoria</label>
              <select v-model="contactForm.category" class="input" required>
                <option value="general">Geral</option>
                <option value="technical">Técnico</option>
                <option value="billing">Cobrança/Assinatura</option>
                <option value="feature">Sugestão de Funcionalidade</option>
              </select>
            </div>

            <div class="form-field">
              <label class="label">Assunto *</label>
              <input
                v-model="contactForm.subject"
                type="text"
                class="input"
                placeholder="Descreva brevemente sua dúvida ou problema"
                required
                :disabled="submitting"
              />
            </div>

            <div class="form-field">
              <label class="label">Mensagem *</label>
              <textarea
                v-model="contactForm.message"
                class="input textarea"
                rows="6"
                placeholder="Descreva sua dúvida, problema ou sugestão em detalhes..."
                required
                :disabled="submitting"
              ></textarea>
            </div>

            <div class="form-info" v-if="authStore.user">
              <p>Você está logado como: <strong>{{ authStore.user?.email }}</strong></p>
            </div>
            <div class="form-info">
              <p class="info-text">Nossa equipe responderá em até 24 horas úteis.</p>
            </div>

            <button type="submit" class="btn primary" :disabled="submitting">
              <Send :size="18" />
              <span>{{ submitting ? 'Enviando...' : 'Enviar Mensagem' }}</span>
            </button>
          </form>

          <div class="contact-alternative">
            <h3>Ou entre em contato diretamente:</h3>
            <div class="contact-methods">
              <a href="mailto:suporte@financeapp.com" class="contact-link">
                <Mail :size="18" />
                <span>suporte@financeapp.com</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- FAQ Section -->
      <div v-if="activeTab === 'faq'" class="content-section">
        <div class="faq-container">
          <div
            v-for="(item, index) in faqItems"
            :key="index"
            class="faq-item"
            :class="{ expanded: expandedFaq === index }"
          >
            <button class="faq-question" @click="toggleFaq(index)">
              <span>{{ item.question }}</span>
              <HelpCircle :size="20" />
            </button>
            <div v-if="expandedFaq === index" class="faq-answer">
              <p>{{ item.answer }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/support.css';
</style>

