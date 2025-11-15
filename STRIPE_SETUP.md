# Configuração do Stripe - Guia Completo

Este guia explica como configurar completamente a integração com Stripe para assinaturas recorrentes, incluindo checkout, cancelamento via Customer Portal e processamento de webhooks.

## Índice

1. [Criar Conta Stripe](#1-criar-conta-stripe)
2. [Obter Chaves da API](#2-obter-chaves-da-api)
3. [Criar Produto e Preço](#3-criar-produto-e-preço)
4. [Configurar Customer Portal](#4-configurar-customer-portal)
5. [Configurar Webhooks](#5-configurar-webhooks)
6. [Configurar Variáveis de Ambiente](#6-configurar-variáveis-de-ambiente)
7. [Testar a Integração](#7-testar-a-integração)
8. [Modo de Teste vs Produção](#8-modo-de-teste-vs-produção)

---

## 1. Criar Conta Stripe

1. Acesse [https://stripe.com](https://stripe.com)
2. Clique em "Sign up" e crie uma conta
3. Complete o processo de verificação da conta
4. Acesse o [Dashboard do Stripe](https://dashboard.stripe.com)

---

## 2. Obter Chaves da API

### Modo de Teste (Development)

1. No Dashboard do Stripe, certifique-se de estar no **modo de teste** (toggle no canto superior direito)
2. Vá em **Developers** → **API keys**
3. Você verá duas chaves:
   - **Publishable key** (começa com `pk_test_...`) - não é necessária para este projeto
   - **Secret key** (começa com `sk_test_...`) - esta é a `STRIPE_SECRET_KEY`

4. Clique em **Reveal test key** para ver a chave secreta completa
5. Copie a chave secreta - você precisará dela para a variável `STRIPE_SECRET_KEY`

### Modo de Produção (Live)

1. No Dashboard do Stripe, altere para o **modo live** (toggle no canto superior direito)
2. Vá em **Developers** → **API keys**
3. Clique em **Reveal live key** para ver a chave secreta
4. Copie a chave secreta - esta será usada em produção

⚠️ **IMPORTANTE**: Nunca compartilhe suas chaves secretas. Use variáveis de ambiente e nunca commite-as no Git.

---

## 3. Criar Produto e Preço

### Criar Produto

1. No Dashboard do Stripe, vá em **Products** → **Add product**
2. Preencha os dados:
   - **Name**: "Plano PRO" (ou o nome que preferir)
   - **Description**: "Plano premium com recursos avançados" (opcional)
3. Clique em **Save product**

### Criar Preço (Price)

1. Na página do produto criado, clique em **Add another price**
2. Configure o preço:
   - **Pricing model**: Recurring
   - **Price**: R$ 29,90 (ou o valor desejado)
   - **Billing period**: Monthly (mensal)
   - **Currency**: BRL (ou a moeda desejada)
3. Clique em **Save price**

4. **Copie o Price ID** - ele começa com `price_...` e será usado na variável `STRIPE_PRICE_ID_PRO`

   Você pode encontrar o Price ID:
   - Na lista de preços do produto
   - Ou na URL quando você clica no preço: `https://dashboard.stripe.com/test/prices/price_xxxxx`

---

## 4. Configurar Customer Portal

O Customer Portal permite que os clientes gerenciem suas assinaturas (cancelar, atualizar método de pagamento, etc.).

1. No Dashboard do Stripe, vá em **Settings** → **Billing** → **Customer portal**
2. Clique em **Activate test link** (para modo de teste) ou **Activate link** (para produção)
3. Configure as opções disponíveis:
   - ✅ **Allow customers to cancel subscriptions** (permitir cancelamento)
   - ✅ **Allow customers to update payment methods** (permitir atualizar pagamento)
   - ✅ **Allow customers to update billing details** (permitir atualizar dados de cobrança)
   - Configure outras opções conforme necessário
4. Clique em **Save changes**

⚠️ **IMPORTANTE**: O Customer Portal deve estar ativado para que o endpoint `/subscription/cancel` funcione corretamente.

---

## 5. Configurar Webhooks

Os webhooks permitem que o Stripe notifique sua aplicação sobre eventos importantes (pagamento confirmado, assinatura cancelada, etc.).

### Para Desenvolvimento Local

Para testar webhooks localmente, você precisa expor seu servidor local. Use uma das seguintes opções:

#### Opção 1: Stripe CLI (Recomendado)

1. Instale o [Stripe CLI](https://stripe.com/docs/stripe-cli)
2. Autentique-se:
   ```bash
   stripe login
   ```
3. Em um terminal separado, inicie o servidor de desenvolvimento do backend
4. Em outro terminal, execute:
   ```bash
   stripe listen --forward-to localhost:8000/webhooks/stripe
   ```
5. O Stripe CLI mostrará um webhook signing secret (começa com `whsec_...`)
6. Use este secret na variável `STRIPE_WEBHOOK_SECRET` para desenvolvimento

#### Opção 2: ngrok

1. Instale o [ngrok](https://ngrok.com/)
2. Inicie seu servidor backend local na porta 8000
3. Em outro terminal, execute:
   ```bash
   ngrok http 8000
   ```
4. Copie a URL HTTPS fornecida pelo ngrok (ex: `https://abc123.ngrok.io`)
5. Continue com os passos abaixo usando esta URL

### Configurar Webhook no Stripe Dashboard

1. No Dashboard do Stripe, vá em **Developers** → **Webhooks**
2. Clique em **Add endpoint**
3. Configure o endpoint:
   - **Endpoint URL**: 
     - Desenvolvimento: `https://seu-ngrok-url.ngrok.io/webhooks/stripe` (se usando ngrok)
     - Produção: `https://seudominio.com/webhooks/stripe`
   - **Description**: "Finance App Webhooks" (opcional)
4. Clique em **Add endpoint**
5. Na seção **Events to send**, selecione os seguintes eventos:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
6. Clique em **Add events** e depois em **Save**
7. **Copie o Signing secret** - ele começa com `whsec_...` e será usado na variável `STRIPE_WEBHOOK_SECRET`

   Você pode encontrar o Signing secret:
   - Na página do webhook criado, clique em **Reveal** ao lado de "Signing secret"
   - Ou na lista de webhooks, clique no webhook e veja os detalhes

---

## 6. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto `finance_backend` (ou onde o backend lê as variáveis de ambiente) com as seguintes variáveis:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_ID_PRO=price_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Stripe URLs (Development)
STRIPE_SUCCESS_URL=http://localhost:3000/subscription/success
STRIPE_CANCEL_URL=http://localhost:3000/subscription/cancel
STRIPE_RETURN_URL=http://localhost:3000/subscription
```

### Para Produção

```env
# Stripe Configuration (Live mode)
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_ID_PRO=price_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Stripe URLs (Production)
STRIPE_SUCCESS_URL=https://seudominio.com/subscription/success
STRIPE_CANCEL_URL=https://seudominio.com/subscription/cancel
STRIPE_RETURN_URL=https://seudominio.com/subscription
```

⚠️ **IMPORTANTE**: 
- Nunca commite o arquivo `.env` no Git
- Use diferentes chaves para desenvolvimento (test) e produção (live)
- O `STRIPE_WEBHOOK_SECRET` é diferente para cada endpoint de webhook criado

---

## 7. Testar a Integração

### Testar Checkout

1. Inicie o servidor backend e frontend
2. Faça login na aplicação
3. Navegue até a página de assinatura
4. Clique em "Tornar-se PRO"
5. Você será redirecionado para o Stripe Checkout
6. Use um cartão de teste do Stripe:
   - **Número**: `4242 4242 4242 4242`
   - **Data de expiração**: Qualquer data futura (ex: `12/34`)
   - **CVC**: Qualquer 3 dígitos (ex: `123`)
   - **CEP**: Qualquer CEP válido (ex: `12345-678`)
7. Complete o pagamento
8. Você deve ser redirecionado de volta para a aplicação com status de sucesso
9. Verifique se o usuário foi atualizado para PRO no banco de dados

### Testar Cancelamento

1. Com um usuário PRO, navegue até a página de assinatura
2. Clique em "Gerenciar Assinatura"
3. Você será redirecionado para o Customer Portal do Stripe
4. Clique em "Cancel subscription"
5. Confirme o cancelamento
6. Você será redirecionado de volta para a aplicação
7. Verifique se o usuário foi rebaixado para USER no banco de dados
8. Verifique se uma notificação foi criada

### Testar Webhooks

1. Use o Stripe CLI para monitorar eventos:
   ```bash
   stripe listen --forward-to localhost:8000/webhooks/stripe
   ```
2. Realize ações na aplicação (checkout, cancelamento)
3. Verifique os logs do Stripe CLI para ver os eventos sendo enviados
4. Verifique os logs do backend para confirmar que os eventos estão sendo processados

### Cartões de Teste do Stripe

O Stripe fornece vários cartões de teste para diferentes cenários:

- **Sucesso**: `4242 4242 4242 4242`
- **Falha de autenticação**: `4000 0025 0000 3155`
- **Cartão recusado**: `4000 0000 0000 0002`
- **Fundos insuficientes**: `4000 0000 0000 9995`

Veja mais em: [https://stripe.com/docs/testing](https://stripe.com/docs/testing)

---

## 8. Modo de Teste vs Produção

### Modo de Teste (Development)

- Use chaves que começam com `sk_test_` e `pk_test_`
- Use Price IDs criados no modo de teste
- Use webhook secrets do modo de teste
- Não há cobranças reais
- Ideal para desenvolvimento e testes

### Modo de Produção (Live)

- Use chaves que começam com `sk_live_` e `pk_live_`
- Use Price IDs criados no modo live
- Use webhook secrets do modo live
- Cobranças reais são processadas
- Requer conta Stripe verificada e ativada

### Migração de Teste para Produção

1. Crie o produto e preço novamente no modo live
2. Configure o Customer Portal no modo live
3. Crie um novo endpoint de webhook no modo live
4. Atualize todas as variáveis de ambiente com as chaves live
5. Teste cuidadosamente antes de ativar para usuários reais

---

## Troubleshooting

### Erro: "Stripe não configurado corretamente"

- Verifique se todas as variáveis de ambiente estão definidas
- Verifique se as chaves estão corretas (sem espaços extras)
- Reinicie o servidor após alterar variáveis de ambiente

### Erro: "Invalid signature" no webhook

- Verifique se o `STRIPE_WEBHOOK_SECRET` está correto
- Certifique-se de usar o secret correto para o endpoint correto
- Se usando Stripe CLI, use o secret mostrado pelo comando `stripe listen`

### Webhook não está sendo recebido

- Verifique se o endpoint está acessível publicamente (use ngrok ou similar em dev)
- Verifique se a URL do webhook no Stripe Dashboard está correta
- Verifique os logs do Stripe Dashboard em **Developers** → **Webhooks** → **Seu webhook** → **Logs**

### Customer Portal não funciona

- Certifique-se de que o Customer Portal está ativado no Stripe Dashboard
- Verifique se o usuário tem um `stripe_customer_id` válido
- Verifique se há uma assinatura ativa associada ao customer

### Assinatura não atualiza após pagamento

- Verifique se o webhook está configurado corretamente
- Verifique se os eventos corretos estão selecionados no webhook
- Verifique os logs do backend para erros ao processar webhooks
- Verifique se o `stripe_customer_id` está sendo salvo corretamente no banco

---

## Recursos Adicionais

- [Documentação do Stripe](https://stripe.com/docs)
- [Stripe Checkout](https://stripe.com/docs/payments/checkout)
- [Customer Portal](https://stripe.com/docs/billing/subscriptions/integrating-customer-portal)
- [Webhooks](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Cartões de Teste](https://stripe.com/docs/testing)

---

## Suporte

Se encontrar problemas, verifique:
1. Os logs do backend
2. Os logs do Stripe Dashboard (webhooks)
3. A documentação oficial do Stripe
4. Os logs do Stripe CLI (se usando)

