"""
Módulo para verificação e disparo de alertas baseados em indicadores técnicos.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.market.technical_analysis import get_technical_analysis
from app.core.market.data_fetcher import get_historical_data
from app.core.email_service import send_alert_email
from app.core.notification_service import create_notification
from app.db.models import NotificationType


def check_and_trigger_alerts(db: Session):
    """
    Verifica todos os alertas ativos e dispara se as condições forem atendidas.
    Implementa checagem de cruzamento (D-1 vs D-0) para maior precisão.
    Apenas alertas de usuários PRO ou ADMIN são processados (com envio de email).
    """
    from app.db.models import Alert, User, UserRole
    
    # Puxa APENAS alertas de usuários PRO ou ADMIN (que podem receber emails)
    active_alerts = db.query(Alert).join(User).filter(
        Alert.is_active == True,
        User.role.in_([UserRole.PRO, UserRole.ADMIN])
    ).all()
    
    if not active_alerts:
        return 0

    triggered_count = 0
    
    # Agrupa alertas por ticker para evitar buscas repetidas
    alerts_by_ticker = {}
    for alert in active_alerts:
        if alert.ticker not in alerts_by_ticker:
            alerts_by_ticker[alert.ticker] = []
        alerts_by_ticker[alert.ticker].append(alert)
        
    for ticker, alerts in alerts_by_ticker.items():
        try:
            # Separar alertas de preço dos alertas de indicadores técnicos
            price_alerts = [a for a in alerts if a.indicator_type == "PRICE"]
            indicator_alerts = [a for a in alerts if a.indicator_type != "PRICE"]
            
            # Processar alertas de indicadores técnicos (lógica existente)
            if indicator_alerts:
                # Puxa a análise técnica completa, usando '3mo' para garantir D-1 e D-0
                analysis_data = get_technical_analysis(ticker, period="3mo")
                
                if len(analysis_data) >= 2:
                    # Pega os dois últimos dias com dados (D-0: Hoje, D-1: Ontem)
                    data_d0 = analysis_data[-1]
                    data_d1 = analysis_data[-2]

                    for alert in indicator_alerts:
                        result = _process_indicator_alert(alert, data_d0, data_d1, db, User, UserRole)
                        if result:
                            triggered_count += 1
            
            # Processar alertas de preço (nova lógica)
            if price_alerts:
                result = _process_price_alerts(price_alerts, ticker, db, User, UserRole)
                if result:
                    triggered_count += result
                    
        except Exception as e:
            # Não pode quebrar o loop por um erro em um ticker
            print(f"Erro ao verificar alerta para o ticker {ticker}: {e}")
            continue

    db.commit()
    return triggered_count


def _process_indicator_alert(alert, data_d0, data_d1, db, User, UserRole):
    """Processa um alerta de indicador técnico."""
    triggered_count = 0
    
    # Inicializa valores D-0 e D-1 para o indicador/preço
    value_d0 = None
    value_d1 = None
    target_line = None  # Para BBANDS crossover
    indicator_name = None  # Nome do indicador para notificações
    
    # --- EXTRAÇÃO DE VALORES ---
    if alert.indicator_type == "RSI":
        value_d0 = data_d0.get('RSI_14')
        value_d1 = data_d1.get('RSI_14')
        indicator_name = "RSI (14)"
    elif alert.indicator_type == "STOCHASTIC":
        # Usamos o %K para cruzamento do STOCHASTIC
        value_d0 = data_d0.get('STOCHk_14_3_3')
        value_d1 = data_d1.get('STOCHk_14_3_3')
        indicator_name = "Stochastic %K"
    elif alert.indicator_type == "MACD":
        # Para MACD, precisamos de 4 valores (MACD Line e Signal Line, D-0 e D-1)
        macd_d0 = data_d0.get('MACD_12_26_9')
        macd_d1 = data_d1.get('MACD_12_26_9')
        macds_d0 = data_d0.get('MACDs_12_26_9')
        macds_d1 = data_d1.get('MACDs_12_26_9')
        indicator_name = "MACD Line vs Signal"
    elif alert.indicator_type == "BBANDS":
        # Para BBANDS, o valor a ser checado é o preço de fechamento
        value_d0 = data_d0.get('close')
        value_d1 = data_d1.get('close')
        indicator_name = "Preço de Fechamento"
    else:
        return 0  # Tipo de alerta desconhecido, pula

    
    # --- VALIDAÇÃO DE VALORES ---
    
    if alert.indicator_type != "MACD" and (value_d0 is None or value_d1 is None):
        return 0
    if alert.indicator_type == "MACD" and not all([macd_d0, macd_d1, macds_d0, macds_d1]):
        return 0
    
    trigger_condition = False
    
    # --- PREPARAÇÃO DE VALORES (DECIMAL) ---
    threshold = Decimal(str(alert.threshold_value)) if alert.threshold_value else None
    
    if value_d0 is not None:
        val_d0_dec = Decimal(str(value_d0))
    if value_d1 is not None:
        val_d1_dec = Decimal(str(value_d1))

    
    # --- LÓGICA 1: CHECAGEM SIMPLES (GREATER_THAN / LESS_THAN) ---
    if alert.condition in ["GREATER_THAN", "LESS_THAN"]:
        # Apenas verifica a condição no ponto atual (D-0)
        if threshold is None:
            return 0
        if alert.condition == "GREATER_THAN" and val_d0_dec > threshold:
            trigger_condition = True
        elif alert.condition == "LESS_THAN" and val_d0_dec < threshold:
            trigger_condition = True



    # --- LÓGICA 2: CHECAGEM DE CROSSOVER (CROSS_ABOVE / CROSS_BELOW) ---
    elif alert.condition in ["CROSS_ABOVE", "CROSS_BELOW"]:
        
        if alert.indicator_type in ["RSI", "STOCHASTIC"]:
            # CROSSOVER CONTRA UM THRESHOLD FIXO
            if threshold is None:
                return 0
            if alert.condition == "CROSS_ABOVE" and val_d1_dec <= threshold and val_d0_dec > threshold:
                trigger_condition = True
            elif alert.condition == "CROSS_BELOW" and val_d1_dec >= threshold and val_d0_dec < threshold:
                trigger_condition = True
                
        elif alert.indicator_type == "MACD":
            # CROSSOVER MACD LINE vs SIGNAL LINE
            macd_d0_dec = Decimal(str(macd_d0))
            macd_d1_dec = Decimal(str(macd_d1))
            macds_d0_dec = Decimal(str(macds_d0))
            macds_d1_dec = Decimal(str(macds_d1))

            # CROSS_ABOVE: MACD Line (D-1) era ABAIXO da Signal Line (D-1) E MACD Line (D-0) é ACIMA da Signal Line (D-0)
            if alert.condition == "CROSS_ABOVE" and macd_d1_dec <= macds_d1_dec and macd_d0_dec > macds_d0_dec:
                trigger_condition = True
            # CROSS_BELOW: MACD Line (D-1) era ACIMA da Signal Line (D-1) E MACD Line (D-0) é ABAIXO da Signal Line (D-0)
            elif alert.condition == "CROSS_BELOW" and macd_d1_dec >= macds_d1_dec and macd_d0_dec < macds_d0_dec:
                trigger_condition = True
                
        elif alert.indicator_type == "BBANDS":
            # CROSSOVER DO PREÇO (close) CONTRA AS BANDAS DE BOLLINGER (BBU ou BBL)
            bbu_d0 = data_d0.get('BBU_20_2.0')
            bbu_d1 = data_d1.get('BBU_20_2.0')
            bbl_d0 = data_d0.get('BBL_20_2.0')
            bbl_d1 = data_d1.get('BBL_20_2.0')
            
            if bbu_d0 is None or bbu_d1 is None or bbl_d0 is None or bbl_d1 is None:
                return 0
                
            bbu_d0_dec = Decimal(str(bbu_d0))
            bbu_d1_dec = Decimal(str(bbu_d1))
            bbl_d0_dec = Decimal(str(bbl_d0))
            bbl_d1_dec = Decimal(str(bbl_d1))
            
            if alert.condition == "CROSS_ABOVE":
                # CROSS_ABOVE: Preço cruza BBU
                if val_d1_dec <= bbu_d1_dec and val_d0_dec > bbu_d0_dec:
                    target_line = "Banda Superior (BBU)"
                    trigger_condition = True
            elif alert.condition == "CROSS_BELOW":
                # CROSS_BELOW: Preço cruza BBL
                if val_d1_dec >= bbl_d1_dec and val_d0_dec < bbl_d0_dec:
                    target_line = "Banda Inferior (BBL)"
                    trigger_condition = True

    # --- DISPARO E NOTIFICAÇÃO ---
    if trigger_condition:
        _trigger_alert(alert, indicator_name, val_d0_dec, val_d1_dec, threshold, target_line, data_d0, data_d1, db, User, UserRole)
        return 1
    
    return 0


def _process_price_alerts(price_alerts, ticker, db, User, UserRole):
    """Processa alertas de preço."""
    triggered_count = 0
    # Buscar dados históricos para pegar preços de D-0 e D-1
    historical_data = get_historical_data(ticker, period="3mo")
    
    if len(historical_data) < 2:
        # Se não temos dados históricos suficientes, tentar usar apenas o preço atual
        # Mas para crossover precisamos de D-1, então vamos pular se não tiver
        for alert in price_alerts:
            if alert.condition in ["CROSS_ABOVE", "CROSS_BELOW"]:
                continue  # Precisa de D-1 para crossover
            
            # Para GREATER_THAN/LESS_THAN, podemos usar apenas o preço atual
            from app.core.market.price_cache import get_current_price
            current_price = get_current_price(ticker, db, cache_threshold_seconds=0)
            
            if current_price is None:
                continue
            
            threshold = Decimal(str(alert.threshold_value)) if alert.threshold_value else None
            if threshold is None:
                continue
            
            current_price_dec = Decimal(str(current_price))
            trigger_condition = False
            
            if alert.condition == "GREATER_THAN" and current_price_dec > threshold:
                trigger_condition = True
            elif alert.condition == "LESS_THAN" and current_price_dec < threshold:
                trigger_condition = True
            
            if trigger_condition:
                _trigger_price_alert(alert, current_price_dec, threshold, None, db, User, UserRole)
                triggered_count += 1
        
        return triggered_count
    
    # Pega os dois últimos dias com dados (D-0: Hoje, D-1: Ontem)
    data_d0 = historical_data[-1]
    data_d1 = historical_data[-2]
    
    price_d0 = data_d0.get('close')
    price_d1 = data_d1.get('close')
    
    if price_d0 is None or price_d1 is None:
        return 0
    
    price_d0_dec = Decimal(str(price_d0))
    price_d1_dec = Decimal(str(price_d1))
    
    for alert in price_alerts:
        threshold = Decimal(str(alert.threshold_value)) if alert.threshold_value else None
        if threshold is None:
            continue
        
        trigger_condition = False
        
        # --- LÓGICA 1: CHECAGEM SIMPLES (GREATER_THAN / LESS_THAN) ---
        if alert.condition in ["GREATER_THAN", "LESS_THAN"]:
            if alert.condition == "GREATER_THAN" and price_d0_dec > threshold:
                trigger_condition = True
            elif alert.condition == "LESS_THAN" and price_d0_dec < threshold:
                trigger_condition = True
        
        # --- LÓGICA 2: CHECAGEM DE CROSSOVER (CROSS_ABOVE / CROSS_BELOW) ---
        elif alert.condition in ["CROSS_ABOVE", "CROSS_BELOW"]:
            if alert.condition == "CROSS_ABOVE" and price_d1_dec <= threshold and price_d0_dec > threshold:
                trigger_condition = True
            elif alert.condition == "CROSS_BELOW" and price_d1_dec >= threshold and price_d0_dec < threshold:
                trigger_condition = True
        
        if trigger_condition:
            _trigger_price_alert(alert, price_d0_dec, threshold, price_d1_dec, db, User, UserRole)
            triggered_count += 1
    
    return triggered_count


def _trigger_price_alert(alert, price_d0_dec, threshold, price_d1_dec, db, User, UserRole):
    """Dispara um alerta de preço."""
    user = db.query(User).filter(User.id == alert.user_id).first()
    
    # A checagem de role já foi feita no início (query), mas garantimos aqui também
    if user and user.email and user.role in [UserRole.PRO, UserRole.ADMIN]:
        subject = f"🚨 ALERTA DE PREÇO DISPARADO: {alert.ticker}"
        
        if alert.condition in ["CROSS_ABOVE", "CROSS_BELOW"] and price_d1_dec is not None:
            action = "cruzou para CIMA de" if alert.condition == "CROSS_ABOVE" else "cruzou para BAIXO de"
            body = (
                f"Seu alerta de PREÇO para o ativo {alert.ticker} foi atingido!\n\n"
                f"O preço {action} R$ {threshold.quantize(Decimal('0.01'))}:\n"
                f"Preço D-1: R$ {price_d1_dec.quantize(Decimal('0.01'))} (Antes do cruzamento)\n"
                f"Preço D-0: R$ {price_d0_dec.quantize(Decimal('0.01'))} (Após o cruzamento)\n\n"
                f"O alerta foi desativado automaticamente para evitar spam. Acesse o app para reativar."
            )
        else:
            # Alerta simples de GREATER_THAN / LESS_THAN
            condition_text = "ultrapassou" if alert.condition == "GREATER_THAN" else "caiu abaixo de"
            body = (
                f"Seu alerta de PREÇO para {alert.ticker} foi atingido!\n\n"
                f"O preço {condition_text} R$ {threshold.quantize(Decimal('0.01'))}:\n"
                f"Preço Atual: R$ {price_d0_dec.quantize(Decimal('0.01'))}\n\n"
                f"O alerta foi desativado automaticamente para evitar spam. Acesse o app para reativar."
            )
        
        from app.core.email_service import send_alert_email
        send_alert_email(user.email, subject, body)

    # Cria notificação in-app e push
    notification_title = f"🚨 Alerta de Preço: {alert.ticker}"
    notification_message = f"Preço {alert.condition.replace('_', ' ').lower()} R$ {threshold.quantize(Decimal('0.01'))}"
    
    create_notification(
        db=db,
        user_id=alert.user_id,
        notification_type=NotificationType.ALERT_TRIGGERED,
        title=notification_title,
        message=notification_message,
        data={
            "alert_id": alert.id,
            "ticker": alert.ticker,
            "indicator_type": alert.indicator_type,
            "condition": alert.condition,
            "threshold_value": str(alert.threshold_value) if alert.threshold_value else None,
            "current_price": str(price_d0_dec.quantize(Decimal('0.01')))
        },
        send_push=True
    )

    # Atualiza o DB
    alert.is_active = False 
    alert.triggered_at = datetime.now()
    db.add(alert)


def _trigger_alert(alert, indicator_name, val_d0_dec, val_d1_dec, threshold, target_line, data_d0, data_d1, db, User, UserRole):
    """Dispara um alerta de indicador técnico (lógica existente)."""
    user = db.query(User).filter(User.id == alert.user_id).first()
    
    # A checagem de role já foi feita no início (query), mas garantimos aqui também
    if user and user.email and user.role in [UserRole.PRO, UserRole.ADMIN]:
        subject = f"🚨 ALERTA DISPARADO: {alert.ticker} - {alert.indicator_type}"
        
        if alert.condition in ["CROSS_ABOVE", "CROSS_BELOW"]:
            if alert.indicator_type == "MACD":
                # Para MACD, mostrar valores de MACD Line e Signal
                macd_d0 = data_d0.get('MACD_12_26_9')
                macd_d1 = data_d1.get('MACD_12_26_9')
                macds_d0 = data_d0.get('MACDs_12_26_9')
                macds_d1 = data_d1.get('MACDs_12_26_9')
                macd_d0_dec = Decimal(str(macd_d0))
                macd_d1_dec = Decimal(str(macd_d1))
                macds_d0_dec = Decimal(str(macds_d0))
                macds_d1_dec = Decimal(str(macds_d1))
                action = "cruzou para CIMA da" if alert.condition == "CROSS_ABOVE" else "cruzou para BAIXO da"
                
                body = (
                    f"Seu alerta de CRUZAMENTO para o ativo {alert.ticker} foi atingido!\n\n"
                    f"O indicador {indicator_name} {action} Linha de Sinal:\n"
                    f"D-1 (Antes do cruzamento):\n"
                    f"  MACD Line: {macd_d1_dec.quantize(Decimal('0.0001'))}\n"
                    f"  Signal Line: {macds_d1_dec.quantize(Decimal('0.0001'))}\n"
                    f"D-0 (Após o cruzamento):\n"
                    f"  MACD Line: {macd_d0_dec.quantize(Decimal('0.0001'))}\n"
                    f"  Signal Line: {macds_d0_dec.quantize(Decimal('0.0001'))}\n\n"
                    f"O alerta foi desativado automaticamente para evitar spam. Acesse o app para reativar."
                )
            elif alert.indicator_type == "BBANDS":
                target = target_line if target_line else "Banda"
                action = "cruzou para CIMA da" if alert.condition == "CROSS_ABOVE" else "cruzou para BAIXO da"
                
                body = (
                    f"Seu alerta de CRUZAMENTO para o ativo {alert.ticker} foi atingido!\n\n"
                    f"O {indicator_name} {action} {target}:\n"
                    f"Valor D-1: {val_d1_dec.quantize(Decimal('0.0001'))} (Antes do cruzamento)\n"
                    f"Valor D-0: {val_d0_dec.quantize(Decimal('0.0001'))} (Após o cruzamento)\n\n"
                    f"O alerta foi desativado automaticamente para evitar spam. Acesse o app para reativar."
                )
            else:
                # RSI ou STOCHASTIC
                target = str(alert.threshold_value)
                action = "cruzou para CIMA do" if alert.condition == "CROSS_ABOVE" else "cruzou para BAIXO do"
                
                body = (
                    f"Seu alerta de CRUZAMENTO para o ativo {alert.ticker} foi atingido!\n\n"
                    f"O indicador {indicator_name} {action} {target}:\n"
                    f"Valor D-1: {val_d1_dec.quantize(Decimal('0.0001'))} (Antes do cruzamento)\n"
                    f"Valor D-0: {val_d0_dec.quantize(Decimal('0.0001'))} (Após o cruzamento)\n\n"
                    f"O alerta foi desativado automaticamente para evitar spam. Acesse o app para reativar."
                )
        else:
            # Alerta simples de GREATER_THAN / LESS_THAN
            body = (
                f"Seu alerta de {alert.condition} para {alert.ticker} foi atingido!\n\n"
                f"Indicador: {indicator_name}\n"
                f"Valor Limite: {alert.threshold_value}\n"
                f"Valor Atual: {val_d0_dec.quantize(Decimal('0.0001'))}\n\n"
                f"O alerta foi desativado automaticamente para evitar spam. Acesse o app para reativar."
            )
        
        from app.core.email_service import send_alert_email
        send_alert_email(user.email, subject, body)

    # Cria notificação in-app e push
    notification_title = f"🚨 Alerta Disparado: {alert.ticker}"
    notification_message = f"{alert.indicator_type} {alert.condition.replace('_', ' ').lower()}"
    if alert.threshold_value:
        notification_message += f" ({alert.threshold_value})"
    
    create_notification(
        db=db,
        user_id=alert.user_id,
        notification_type=NotificationType.ALERT_TRIGGERED,
        title=notification_title,
        message=notification_message,
        data={
            "alert_id": alert.id,
            "ticker": alert.ticker,
            "indicator_type": alert.indicator_type,
            "condition": alert.condition,
            "threshold_value": str(alert.threshold_value) if alert.threshold_value else None
        },
        send_push=True
    )

    # Atualiza o DB
    alert.is_active = False 
    alert.triggered_at = datetime.now()
    db.add(alert)

